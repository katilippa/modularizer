def closed_question(question: str) -> bool:
    response = ''
    while response.lower() != 'y' and response.lower() != 'yes' and response.lower() != 'n' and response.lower() != 'no':
        response = input(f'{question} (y/n): ')
    if response.lower() == 'n' or response.lower() == 'no':
        return False
    else:
        return True
