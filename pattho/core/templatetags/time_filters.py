from django import template

register = template.Library()

@register.filter
def minutes_to_hours_minutes(total_minutes):
    if total_minutes is None:
        return "0 minutes"
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if hours > 0 and minutes > 0:
        return f"{hours} hrs {minutes} mins"
    elif hours > 0:
        return f"{hours} hrs"
    elif minutes > 0:
        return f"{minutes} mins"
    else:
        return "0 minutes"