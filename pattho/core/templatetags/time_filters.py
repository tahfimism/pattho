from django import template

register = template.Library()

@register.filter
def minutes_to_hours_minutes(total_minutes):
    if total_minutes is None:
        return "0 minutes"
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0 and minutes > 0:
        return f"{hours} hours {minutes} minutes"
    elif hours > 0:
        return f"{hours} hours"
    elif minutes > 0:
        return f"{minutes} minutes"
    else:
        return "0 minutes"