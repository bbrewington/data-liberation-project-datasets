with source as (
    select * from read_xlsx('/Users/brentbrewington/Downloads/24-F-0024_FY16-FY23_Final.xlsx', all_varchar = true)
),

renamed as (
    select
        "Situation Identifier (F1)" as f1_situation_identifier,
        "FAP UIC (F2)" as f2_fap_uic,
        "US State Alpha Code (F3)" as f3_us_state_alpha_code,
        "Country Code (F4)" as f4_country_code,
        "Incident Report Date (F5)" as f5_incident_report_date,
        "Military Service Organization Code (F6)" as f6_military_service_organization_code,
        "Organization Name Text (F7)" as f7_organization_name_text,
        "Victim Type Code (F8)" as f8_victim_type_code,
        "Alleged Abuse Code (F9)" as f9_alleged_abuse_code,
        "Person Status Code (F10)" as f10_person_status_code,
        "Deceased Victim Previously Known to the DoD Central Registry (F11)"
            as f11_deceased_victim_previously_known_to_the_dod_central_registry,
        "Alleged Abuser of Decedent Previously Known to the DoD Central Registry (F12)"
            as f12_alleged_abuser_of_decedent_previously_known_to_the_dod_central_registry,
        "Situation Incident Findings Date (F13A)" as f13a_situation_incident_findings_date,
        "Alleged Abuser Previously Known to the Submitting Service CR in Met Criteria Case as Abuser (F13B)"
            as f13b_alleged_abuser_previously_known_to_the_submitting_service_cr_in_met_criteria_case_as_abuser,
        "Incident Did Not Meet Criteria for Abuse (F13C)" as f13c_incident_did_not_meet_criteria_for_abuse,
        "Incident Did Not Meet Criteria for Abuse But Referred for Services (F13D)"
            as f13d_incident_did_not_meet_criteria_for_abuse_but_referred_for_services,
        "Incident Met Criteria for Abuse (F13E)" as f13e_incident_met_criteria_for_abuse,
        "Incident Met Criteria – Date Transferred In from another location (F13F)"
            as f13f_incident_met_criteria_date_transferred_in_from_another_location,
        "Incident Met Criteria – Date the incident transferred out to another location (F13G)"
            as f13g_incident_met_criteria_date_the_incident_transferred_out_to_another_location,
        "Incident Met Criteria – Closed Date (F13H)" as f13h_incident_met_criteria_closed_date,
        "Person Association Reason Code (F14)" as f14_person_association_reason_code,
        "Extrafamilial Caregiver Type Code (F15)" as f15_extrafamilial_caregiver_type_code,
        "Personnel Resource Type Code (F18)" as f18_personnel_resource_type_code,
        "Uniformed Service Organization Code (F19)" as f19_uniformed_service_organization_code,
        "Military Service Organization Component Type Code (F20)"
            as f20_military_service_organization_component_type_code,
        "Pay Plan Code (F21)" as f21_pay_plan_code,
        "Person-Situation Role Code (F23)" as f23_person_situation_role_code,
        "Victim Person Birth Year (F26)" as f26_victim_person_birth_year,
        "Sex Category Code (F27)" as f27_sex_category_code,
        "Personnel Resource Type Code (F28)" as f28_personnel_resource_type_code,
        "Substance Involvement (F29)" as f29_substance_involvement,
        "Emotional Abuse Severity Code (F30A)" as f30a_emotional_abuse_severity_code,
        "Neglect Severity Code (F30B)" as f30b_neglect_severity_code,
        "Physical Abuse Severity Code (F30C)" as f30c_physical_abuse_severity_code,
        "Sexual Abuse Severity Code (F30D)" as f30d_sexual_abuse_severity_code,
        "At Case Closure, Clinical Intervention Provided by (F31)"
            as f31_at_case_closure_clinical_intervention_provided_by,
        "Alleged Abuser Person Birth Year (F34)" as f34_alleged_abuser_person_birth_year,
        "Alleged Abuser Sex Category Code (F35)" as f35_alleged_abuser_sex_category_code,
        "Personnel Resource Type Code (F36)" as f36_personnel_resource_type_code,
        "Military Service Organizational Code (F37)" as f37_military_service_organizational_code,
        "Military Service Organizational Component Type Code (F38)"
            as f38_military_service_organizational_component_type_code,
        "Pay Plan Code (F39)" as f39_pay_plan_code,
        "Substance Involvement (F43)" as f43_substance_involvement,
        "At Case Closure Clinical Intervention Provided By (F44)"
            as f44_at_case_closure_clinical_intervention_provided_by
    from source
),

cleaned as (
    select *
        replace(
            try_strptime(f5_incident_report_date, '%Y%m%d')::DATE as f5_incident_report_date,
            try_strptime(f13a_situation_incident_findings_date, '%Y%m%d')::DATE as f13a_situation_incident_findings_date,
            try_strptime(f13f_incident_met_criteria_date_transferred_in_from_another_location, '%Y%m%d')::DATE as f13f_incident_met_criteria_date_transferred_in_from_another_location,
            try_strptime(f13g_incident_met_criteria_date_the_incident_transferred_out_to_another_location, '%Y%m%d')::DATE as f13g_incident_met_criteria_date_the_incident_transferred_out_to_another_location,
            try_strptime(f13h_incident_met_criteria_closed_date, '%Y%m%d')::DATE as f13h_incident_met_criteria_closed_date,
            TRY(f26_victim_person_birth_year::INTEGER) as f26_victim_person_birth_year,
            TRY(f34_alleged_abuser_person_birth_year::INTEGER) as f34_alleged_abuser_person_birth_year
        )
    from renamed
)

select * from cleaned
