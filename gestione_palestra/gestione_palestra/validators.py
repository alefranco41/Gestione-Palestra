from datetime import datetime
import pytz
from django.core.exceptions import ValidationError
import re

today = datetime.now(pytz.timezone('Europe/Rome'))

def validate_age_of_birth(value):

    if value > today.date():
        raise ValidationError('The date you inserted is in the future.')
    
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

    if age > 100:
        raise ValidationError('Please insert a legitimate date of birth.')
    
def validate_name(value):
    if not re.match("^[a-zA-Z0-9]*$", value):
        raise ValidationError('Only alphanumeric characters are allowed for first and last names.')


def validate_heigth(value):
    try:
        value = int(value)
    except ValueError:
        raise ValidationError('Only integer values are allowed for heigth.')
    
    if value > 230 or value < 55:
        raise ValidationError('Heigth must be an integer between 55 and 230')

def validate_weigth(value):
    try:
        value = int(value)
    except ValueError:
        raise ValidationError('Only integer values are allowed for weigth.')
    
    if value > 150 or value < 50:
        raise ValidationError('Weigth must be an integer value between 50 and 150')


def validate_number(value):
    try:
        value = int(value)
    except ValueError:
        raise ValidationError('Only integer values are allowed for duration.')
    
    if value > 150 or value < 50:
        raise ValidationError('Duration must be an integer value between 0 and 120')


def validate_text(value):
    pass