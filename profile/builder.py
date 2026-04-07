from parser_v1.section_parsers import parse_date, parse_skills
from scoring.jd_skill_extractor import SKILL_ALIASES


CONFIDENCE_SCORES = {
	"high": 0.9,
	"medium": 0.7,
	"low": 0.4,
}

ROLE_WEIGHTS = {
	"intern": 0.5,
	"junior": 0.7,
	"engineer": 1.0,
	"developer": 1.0,
	"analyst": 1.0,
	"senior": 1.3,
	"lead": 1.5,
	"manager": 1.4,
	"principal": 1.6,
	"architect": 1.5,
}

TECH_SKILL_VOCAB = set()
for canonical, aliases in SKILL_ALIASES.items():
	TECH_SKILL_VOCAB.add(canonical.strip().lower())
	for alias in aliases:
		TECH_SKILL_VOCAB.add(alias.strip().lower())


def _safe_float(value, default=0.0):
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _normalize_skill(skill):
	return str(skill).strip().lower()


def _is_technical_skill(skill):
	return _normalize_skill(skill) in TECH_SKILL_VOCAB


def _role_weight(role_value):
	text = str(role_value or "").lower()
	best = 1.0
	for token, weight in ROLE_WEIGHTS.items():
		if token in text and weight > best:
			best = weight
	return best


def _duration_years_between(start, end):
	if not start or not end:
		return 0.0
	months = (end.year - start.year) * 12 + (end.month - start.month)
	if end.day < start.day:
		months -= 1
	if months < 0:
		return 0.0
	return round(months / 12.0, 2)


def _parse_date_range(value):
	if not value:
		return None
	parts = str(value).split(" - ", 1)
	if len(parts) != 2:
		return None
	start = parse_date(parts[0].strip())
	end = parse_date(parts[1].strip())
	if not start or not end or end < start:
		return None
	return (start, end)


def _merged_interval_years(intervals):
	if not intervals:
		return 0.0

	sorted_intervals = sorted(intervals, key=lambda it: it[0])
	merged = [sorted_intervals[0]]

	for start, end in sorted_intervals[1:]:
		last_start, last_end = merged[-1]
		if start <= last_end:
			if end > last_end:
				merged[-1] = (last_start, end)
		else:
			merged.append((start, end))

	total = 0.0
	for start, end in merged:
		total += _duration_years_between(start, end)

	return round(total, 2)


def build_profile(experience_entries, skills):
	"""
	Build an aggregate profile from parsed experience entries and candidate skills.

	Returns:
	{
		"total_experience": float,
		"skill_experience": {"skill": float, ...},
		"avg_confidence": float,
	}
	"""
	experience_entries = experience_entries or []
	provided_skills = skills or []

	total_experience = 0.0
	skill_years = {}
	confidence_values = []
	date_intervals = []
	undated_duration_fallback = 0.0
	role_weighted_experience = 0.0

	for exp in experience_entries:
		if not isinstance(exp, dict):
			continue

		duration_years = _safe_float(exp.get("duration_years"), default=0.0)
		if duration_years < 0:
			duration_years = 0.0

		role_weight = _role_weight(exp.get("role"))
		weighted_duration_years = round(duration_years * role_weight, 2)
		role_weighted_experience += weighted_duration_years

		parsed_range = _parse_date_range(exp.get("date_range", ""))
		if parsed_range:
			date_intervals.append(parsed_range)
		else:
			undated_duration_fallback += duration_years

		confidence_label = str(exp.get("confidence", "low")).strip().lower()
		confidence_values.append(CONFIDENCE_SCORES.get(confidence_label, CONFIDENCE_SCORES["low"]))

		description = str(exp.get("description", "") or "")
		extracted = [s for s in parse_skills(description) if _is_technical_skill(s)]
		if extracted:
			per_skill_years = weighted_duration_years / min(len(extracted), 4)
		else:
			per_skill_years = 0.0

		for skill in extracted:
			normalized = _normalize_skill(skill)
			if not normalized:
				continue
			skill_years[normalized] = round(skill_years.get(normalized, 0.0) + per_skill_years, 2)

	# Keep input skills visible even if no duration got assigned.
	for skill in provided_skills:
		normalized = _normalize_skill(skill)
		if normalized and normalized not in skill_years:
			skill_years[normalized] = 0.0

	avg_confidence = 0.0
	if confidence_values:
		avg_confidence = round(sum(confidence_values) / len(confidence_values), 2)

	merged_dated_years = _merged_interval_years(date_intervals)
	total_experience = round(merged_dated_years + undated_duration_fallback, 2)

	return {
		"total_experience": total_experience,
		"role_weighted_experience": round(role_weighted_experience, 2),
		"skill_experience": dict(sorted(skill_years.items())),
		"avg_confidence": avg_confidence,
	}
