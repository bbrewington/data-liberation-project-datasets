with combined as (
    select * from {{ ref('stg__accidents_2009_2013') }}
    union all by name
    select * from {{ ref('stg__accidents_2014_2022') }}
    union all by name
    select * from {{ ref('stg__accidents_2023') }}
),

cleaned as (
    select *
        replace (
            {{ initcap('day_of_week') }} as day_of_week,
            {{ initcap('name_of_body_of_water') }} as name_of_body_of_water,
            accident_date::DATE as accident_date,
            {{ binary_str_yn('a_vessel_loss') }} as a_vessel_loss,
            {{ binary_int('clear') }} as clear,
            {{ binary_int('cloudy') }} as cloudy,
            {{ binary_int('fog') }} as fog,
            {{ binary_int('hazy') }} as hazy,
            {{ binary_int('rain') }} as rain,
            {{ binary_int('snow') }} as snow,
            case when day_night = -1 then 'day' when day_night = 0 then 'night' else null end as day_night
        ),

        case 
            when accident_date is not null and accident_time is not null then 'Complete'
            when accident_date is not null and accident_time is null then 'Date Only'
            else 'Incomplete'
        end as accident_datetime_completeness,
        case 
            when latitude is not null and longitude is not null then 'Available'
            else 'Not Available'
        end as coordinates_availability,
    from combined
)

select * from cleaned
