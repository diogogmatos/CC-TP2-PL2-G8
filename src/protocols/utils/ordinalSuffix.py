# add ordinal suffix to nr
def ordinalSuffix(num):
    if 4 <= num <= 20:
        suffix = 'th'
    elif num == 1 or (num % 10) == 1:
        suffix = 'st'
    elif num == 2 or (num % 10) == 2:
        suffix = 'nd'
    elif num == 3 or (num % 10) == 3:
        suffix = 'rd'
    else:
        suffix = 'th'
    return str(num) + suffix
