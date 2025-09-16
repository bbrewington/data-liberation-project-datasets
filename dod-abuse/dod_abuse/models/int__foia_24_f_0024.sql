with f9_multivalue_map as (
    SELECT distinct -- note, could probably find a way to do this without distinct, but this works for now
        f9_alleged_abuse_code,
        ARRAY_TO_STRING(
            ARRAY(
                SELECT "desc" as abuse_name 
                FROM {{ ref('dod_fap_6400_codes') }}
                WHERE POSITION(code IN f9_alleged_abuse_code) > 0
                AND field_num = 'f9'
                ORDER BY code
            ), 
            ', '
        ) as abuse_names
    FROM {{ ref('stg__foia_24_f_0024') }}
    WHERE f9_alleged_abuse_code IS NOT NULL
),

cleaned as (
    select
        foia.f1_situation_identifier,
        foia.f2_fap_uic,
        foia.f3_us_state_alpha_code,
        foia.f4_country_code,
        -- country_xref.country_name as f4_country, -- Leaving this out until country code data issue resolved (see README)
        foia.f5_incident_report_date,
        foia.f6_military_service_organization_code,
        code_xref_f6.desc as f6_military_service_organization,
        foia.f7_organization_name_text,
        foia.f8_victim_type_code,
        code_xref_f8.desc as f8_victim_type,
        foia.f9_alleged_abuse_code,
        code_xref_f9.abuse_names as f9_alleged_abuse,
        contains(foia.f9_alleged_abuse_code, 'C') as f9_alleged_abuse_emotional,
        contains(foia.f9_alleged_abuse_code, 'H') as f9_alleged_abuse_neglect,
        contains(foia.f9_alleged_abuse_code, 'I') as f9_alleged_abuse_physical,
        contains(foia.f9_alleged_abuse_code, 'J') as f9_alleged_abuse_sexual,
        foia.f10_person_status_code,
        code_xref_f10.desc as f10_person_status,
        foia.f11_deceased_victim_previously_known_to_the_dod_central_registry,
        foia.f12_alleged_abuser_of_decedent_previously_known_to_the_dod_central_registry,
        foia.f13a_situation_incident_findings_date,
        foia.f13b_alleged_abuser_previously_known_to_the_submitting_service_cr_in_met_criteria_case_as_abuser,
        foia.f13c_incident_did_not_meet_criteria_for_abuse,
        foia.f13d_incident_did_not_meet_criteria_for_abuse_but_referred_for_services,
        foia.f13e_incident_met_criteria_for_abuse,
        foia.f13f_incident_met_criteria_date_transferred_in_from_another_location,
        foia.f13g_incident_met_criteria_date_the_incident_transferred_out_to_another_location,
        foia.f13h_incident_met_criteria_closed_date,
        foia.f14_person_association_reason_code,
        code_xref_f14.desc as f14_person_association_reason,
        code_xref_f14.category as f14_person_association_reason_category,
        foia.f15_extrafamilial_caregiver_type_code,
        code_xref_f15.desc as f15_extrafamilial_caregiver_type,
        foia.f18_personnel_resource_type_code,
        code_xref_f18.desc as f18_personnel_resource_type,
        foia.f19_uniformed_service_organization_code,
        code_xref_f19.desc as f19_uniformed_service_organization,
        foia.f20_military_service_organization_component_type_code,
        code_xref_f20.desc as f20_military_service_organization_component_type,
        foia.f21_pay_plan_code,
        code_xref_f21.desc as f21_pay_plan,
        foia.f23_person_situation_role_code,
        code_xref_f23.desc as f23_person_situation_role,
        foia.f26_victim_person_birth_year,
        foia.f27_sex_category_code,
        code_xref_f27.desc as f27_sex_category,
        foia.f28_personnel_resource_type_code,
        code_xref_f28.desc as f28_personnel_resource_type,
        foia.f29_substance_involvement,
        contains(foia.f29_substance_involvement, 'A') as f29_substance_involvement_alcohol,
        contains(foia.f29_substance_involvement, 'D') as f29_substance_involvement_drug,
        contains(foia.f29_substance_involvement, 'U') as f29_substance_involvement_unknown,
        contains(foia.f29_substance_involvement, 'Z') as f29_substance_involvement_no_substance,
        try(foia.f30a_emotional_abuse_severity_code::INTEGER) as f30a_emotional_abuse_severity_code,
        code_xref_f30a.desc as f30a_emotional_abuse_severity,
        try(foia.f30b_neglect_severity_code::INTEGER) as f30b_neglect_severity_code,
        code_xref_f30b.desc as f30b_neglect_severity,
        try(foia.f30c_physical_abuse_severity_code::INTEGER) as f30c_physical_abuse_severity_code,
        code_xref_f30c.desc as f30c_physical_abuse_severity,
        try(foia.f30d_sexual_abuse_severity_code::INTEGER) as f30d_sexual_abuse_severity_code,
        code_xref_f30d.desc as f30d_sexual_abuse_severity,
        foia.f31_at_case_closure_clinical_intervention_provided_by,
        foia.f34_alleged_abuser_person_birth_year,
        foia.f35_alleged_abuser_sex_category_code,
        code_xref_f35.desc as f35_alleged_abuser_sex_category,
        foia.f36_personnel_resource_type_code,
        code_xref_f36.desc as f36_personnel_resource_type,
        foia.f37_military_service_organizational_code,
        code_xref_f37.desc as f37_military_service_organizational,
        foia.f38_military_service_organizational_component_type_code,
        code_xref_f38.desc as f38_military_service_organizational_component_type,
        foia.f39_pay_plan_code,
        code_xref_f39.desc as f39_pay_plan,
        foia.f43_substance_involvement,
        contains(foia.f43_substance_involvement, 'A') as f43_substance_involvement_alcohol,
        contains(foia.f43_substance_involvement, 'D') as f43_substance_involvement_drug,
        contains(foia.f43_substance_involvement, 'U') as f43_substance_involvement_unknown,
        contains(foia.f43_substance_involvement, 'Z') as f43_substance_involvement_no_substance,
        foia.f44_at_case_closure_clinical_intervention_provided_by,
        contains(foia.f44_at_case_closure_clinical_intervention_provided_by, 'K')
            as f44_at_case_closure_clinical_intervention_provided_by_fap_personnel,
        contains(foia.f44_at_case_closure_clinical_intervention_provided_by, 'Y')
            as f44_at_case_closure_clinical_intervention_provided_by_other_dod_funded_program_or_individual,
        contains(foia.f44_at_case_closure_clinical_intervention_provided_by, 'X')
            as f44_at_case_closure_clinical_intervention_provided_by_non_dod_funded_program_or_individual,
        contains(foia.f44_at_case_closure_clinical_intervention_provided_by, 'Z')
            as f44_at_case_closure_clinical_intervention_provided_by_no_treatment_provided
    from {{ ref('stg__foia_24_f_0024') }} as foia
    -- Leaving this out until country code data issue resolved (see README)
    -- left join {{ ref('country_codes_iso') }} as country_xref
    --     on country_xref.code = foia.f4_country_code
    left join {{'dod_fap_6400_codes'}} as code_xref_f6
        on code_xref_f6.code = foia.f6_military_service_organization_code
        and code_xref_f6.field_num = 'f6'
    left join {{'dod_fap_6400_codes'}} as code_xref_f8
        on code_xref_f8.code = foia.f8_victim_type_code
        and code_xref_f8.field_num = 'f8'
    left join f9_multivalue_map as code_xref_f9
        on code_xref_f9.f9_alleged_abuse_code = foia.f9_alleged_abuse_code
    -- left join {{'dod_fap_6400_codes'}} as code_xref_f9
    --     on code_xref_f9.code = foia.f9_alleged_abuse_code
        -- and code_xref_f9.field_num = 'f9'
    left join {{'dod_fap_6400_codes'}} as code_xref_f10
        on code_xref_f10.code = foia.f10_person_status_code
        and code_xref_f10.field_num = 'f10'
    left join {{'dod_fap_6400_codes'}} as code_xref_f14
        on code_xref_f14.code = foia.f14_person_association_reason_code
        and code_xref_f14.field_num = 'f14'
    left join {{'dod_fap_6400_codes'}} as code_xref_f15
        on code_xref_f15.code = foia.f15_extrafamilial_caregiver_type_code
        and code_xref_f15.field_num = 'f15'
    left join {{'dod_fap_6400_codes'}} as code_xref_f18
        on code_xref_f18.code = foia.f18_personnel_resource_type_code
        and code_xref_f18.field_num = 'f18'
    left join {{'dod_fap_6400_codes'}} as code_xref_f19
        on code_xref_f19.code = foia.f19_uniformed_service_organization_code
        and code_xref_f19.field_num = 'f19'
    left join {{'dod_fap_6400_codes'}} as code_xref_f20
        on code_xref_f20.code = foia.f20_military_service_organization_component_type_code
        and code_xref_f20.field_num = 'f20'
    left join {{'dod_fap_6400_codes'}} as code_xref_f21
        on code_xref_f21.code = foia.f21_pay_plan_code
        and code_xref_f21.field_num = 'f21'
    left join {{'dod_fap_6400_codes'}} as code_xref_f23
        on code_xref_f23.code = foia.f23_person_situation_role_code
        and code_xref_f23.field_num = 'f23'
    left join {{'dod_fap_6400_codes'}} as code_xref_f27
        on code_xref_f27.code = foia.f27_sex_category_code
        and code_xref_f27.field_num = 'f27'
    left join {{'dod_fap_6400_codes'}} as code_xref_f28
        on code_xref_f28.code = foia.f28_personnel_resource_type_code
        and code_xref_f28.field_num = 'f28'
    left join {{'dod_fap_6400_codes'}} as code_xref_f29
        on code_xref_f29.code = foia.f29_substance_involvement
        and code_xref_f29.field_num = 'f29'
    left join {{'dod_fap_6400_codes'}} as code_xref_f30a
        on code_xref_f30a.code = foia.f30a_emotional_abuse_severity_code
    left join {{'dod_fap_6400_codes'}} as code_xref_f30b
        on code_xref_f30b.code = foia.f30b_neglect_severity_code
    left join {{'dod_fap_6400_codes'}} as code_xref_f30c
        on code_xref_f30c.code = foia.f30c_physical_abuse_severity_code
    left join {{'dod_fap_6400_codes'}} as code_xref_f30d
        on code_xref_f30d.code = foia.f30d_sexual_abuse_severity_code
    left join {{'dod_fap_6400_codes'}} as code_xref_f31
        on code_xref_f31.code = foia.f31_at_case_closure_clinical_intervention_provided_by
        and code_xref_f31.field_num = 'f31'
    left join {{'dod_fap_6400_codes'}} as code_xref_f35
        on code_xref_f35.code = foia.f35_alleged_abuser_sex_category_code
        and code_xref_f35.field_num = 'f35'
    left join {{'dod_fap_6400_codes'}} as code_xref_f36
        on code_xref_f36.code = foia.f36_personnel_resource_type_code
        and code_xref_f36.field_num = 'f36'
    left join {{'dod_fap_6400_codes'}} as code_xref_f37
        on code_xref_f37.code = foia.f37_military_service_organizational_code
        and code_xref_f37.field_num = 'f37'
    left join {{'dod_fap_6400_codes'}} as code_xref_f38
        on code_xref_f38.code = foia.f38_military_service_organizational_component_type_code
        and code_xref_f38.field_num = 'f38'
    left join {{'dod_fap_6400_codes'}} as code_xref_f39
        on code_xref_f39.code = foia.f39_pay_plan_code
        and code_xref_f39.field_num = 'f39'
    left join {{'dod_fap_6400_codes'}} as code_xref_f43
        on code_xref_f43.code = foia.f43_substance_involvement
        and code_xref_f43.field_num = 'f43'
    left join {{'dod_fap_6400_codes'}} as code_xref_f44
        on code_xref_f44.code = foia.f44_at_case_closure_clinical_intervention_provided_by
        and code_xref_f44.field_num = 'f44'
),

final as (
    select *,
        (
            f8_victim_type = 'Child' and (f13e_incident_met_criteria_for_abuse in ('Y','N'))
        )::INTEGER as br1_reported_child_abuse_and_neglect_incident,
        case
            when f13e_incident_met_criteria_for_abuse = 'Y' and f8_victim_type = 'Child'
                then (ifnull(f30a_emotional_abuse_severity_code, 0) >= 1)::INTEGER +
                     (ifnull(f30b_neglect_severity_code, 0) >= 1)::INTEGER +
                     (ifnull(f30c_physical_abuse_severity_code, 0) >= 1)::INTEGER +
                     (ifnull(f30d_sexual_abuse_severity_code, 0) >= 1)::INTEGER
            else 0 end
            as br2_met_criteria_child_abuse_and_neglect_incidents
    from cleaned
)

select * from final
