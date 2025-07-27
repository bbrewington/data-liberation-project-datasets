with combined as (
    select * from {{ ref('stg__accidents_2009_2013') }}
    union all by name
    select * from {{ ref('stg__accidents_2014_2022') }}
    union all by name
    select * from {{ ref('stg__accidents_2023') }}
),

replaces as (
    select *
        replace (
            {{ initcap('day_of_week') }} as day_of_week,
            {{ initcap('name_of_body_of_water') }} as name_of_body_of_water,
            accident_date::DATE as accident_date,
            {{ binarify('a_vessel_loss') }} as a_vessel_loss,
            case when day_night = -1 then 'day' when day_night = 0 then 'night' else null end as day_night,
            {{ binarify('hazardous_waters') }} as hazardous_waters,
            {{ binarify('meets_damage_threshold') }} as meets_damage_threshold,
            {{ binarify('meets_injury_threshold') }} as meets_injury_threshold,
        )
    from combined
),

mutate as (
    select *
        exclude(
            clear,
            cloudy,
            fog,
            hazy,
            rain,
            snow
        ),

        {{ binarify('clear') }} as weather_clear,
        {{ binarify('cloudy') }} as weather_cloudy,
        {{ binarify('fog') }} as weather_fog,
        {{ binarify('hazy') }} as weather_hazy,
        {{ binarify('rain') }} as weather_rain,
        {{ binarify('snow') }} as weather_snow,

        case 
            when accident_date is not null and accident_time is not null then 'Complete'
            when accident_date is not null and accident_time is null then 'Date Only'
            else 'Incomplete'
        end as accident_datetime_completeness,
        case 
            when latitude is not null and longitude is not null then 'Available'
            else 'Not Available'
        end as coordinates_availability,
    from replaces
)

select * from mutate
