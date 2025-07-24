{% docs stg__vessels %}
The ReleasableVessels table contains information specific to the vessel, the vessel operator and the events and causes from the perspective of each vessel. Each row in this table represents a vessel.  Information in this table is linked to the ReleasableAccidents table by the field called “BARDID” and to the ReleasableDeaths and ReleasableInjuries tables by the fields called “BARDID”, “Year”, and “VesselID”.
{% enddocs %}
