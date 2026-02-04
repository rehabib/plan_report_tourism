# plans/permissions.py

# Who can VIEW plans created at each level
# PLAN_VIEW_RULES = {
#     "individual": ["individual", "desk", "department"],
#     "desk": ["desk", "department"],
#     "department": ["department", "corporate"],
#     "corporate": ["corporate", "strategic-team"],
#     "state-minister-destination": ["state-minister-destination", "strategic-team"],
#     "state-minister-promotion": ["state-minister-promotion", "strategic-team"],
#     "strategic-team": ["strategic-team", "minister"],
#     "minister": ["minister"],
# }

# # Who can EDIT / DELETE plans
# PLAN_EDIT_RULES = {
#     "DRAFT": ["individual", "desk", "department", "corporate",
#               "state-minister-destination", "state-minister-promotion",
#               "strategic-team", "minister"],

#     "SUBMITTED": [],
#     "IN_REVIEW": [],
#     "APPROVED": [],
#     "REJECTED": [],
# }

# Who can APPROVE at each workflow step
PLAN_APPROVAL_FLOW = {
    "individual": "desk",
    "desk": "department",
    "department": "pillar",  # resolved dynamically

    "corporate": "strategic-team",
    "state-minister-destination": "strategic-team",
    "state-minister-promotion": "strategic-team",

    "strategic-team": "minister",
}
