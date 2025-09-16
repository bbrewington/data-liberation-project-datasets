## Data Issues

### f4_country_code

GM - is in ISO, it's Gambia. Is this supposed to be Guam?
JA - not in ISO, is this Japan?
KO - not in ISO
KS - not in ISO
RK - not in ISO
TU - not in ISO, Is this Turkey? If so, ISO-3166-1-alpha2 code is TR
UK - not in ISO, Is this GB (Great Britain) or UA (Ukraine)?

### f14_person_association_reason_code

BC (154 records) - not in DoDM 6400.01-V2, August 11, 2016
BX (8 records) - not in DoDM 6400.01-V2, August 11, 2016

Valid values for reference:

```csv
field_num,code,desc,category
f14,AD,Parent,Intrafamilial
f14,AA,Spouse,Intrafamilial
f14,AC,Sibling,Intrafamilial
f14,BN,Other Family Member,Intrafamilial
f14,CA,Extrafamilial Caregiver,Extrafamilial
f14,BH,Former spouse,Extrafamilial
f14,BE,Intimate Partner,Extrafamilial
f14,CC,Relationship Unknown,Extrafamilial
```

### f29_substance_involvement

AZ (4428 records) - contains "Z" meaning "No substance involved", but "A" means "Alcohol"
ZD (293 records) - contains "Z" meaning "No substance involved", but "D" means "Drugs"
