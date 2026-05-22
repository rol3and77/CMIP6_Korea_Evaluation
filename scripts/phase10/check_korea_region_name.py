import regionmask

countries = regionmask.defined_regions.natural_earth_v5_0_0.countries_50

print("Searching country names containing Korea...\n")

for number, name, abbrev in zip(countries.numbers, countries.names, countries.abbrevs):
    if "Korea" in name or "Korea" in abbrev:
        print("number:", number)
        print("name:", name)
        print("abbrev:", abbrev)
        print("-" * 40)
