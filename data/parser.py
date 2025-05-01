def parse_temperatures(input:str|list[str], separator=','):
    if type(input) == str:
        temps = input.strip().split(sep=separator)
    else:
        temps = input
    return list(map(lambda x: float(x), temps))
    