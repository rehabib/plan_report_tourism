def get_kpi_target(kpi, plan):
    """
    Returns the correct target based on plan type
    """
    if plan.plan_type == "yearly":
        return kpi.target

    if plan.plan_type == "quarterly":
        # example: use Q1–Q4 based on plan quarter
        if plan.quarter_number == 1:
            return kpi.target_q1
        elif plan.quarter_number == 2:
            return kpi.target_q2
        elif plan.quarter_number == 3:
            return kpi.target_q3
        elif plan.quarter_number == 4:
            return kpi.target_q4

    # monthly / weekly
    return kpi.target
