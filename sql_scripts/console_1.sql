create table public.lead
(
    lead_id                                        varchar(8)                                               not null
        primary key,
    lead_name                                      varchar(64)                                              not null,
    lead_email                                     varchar(64)                                              not null,
    lead_phone_number                              varchar(22)                                              not null,
    what_services_are_they_interested_in           varchar                  default '{}'::character varying not null,
    details_on_what_service_they_are_interested_in varchar                                                  not null,
    miscellaneous_notes                            varchar                                                  not null,
    how_did_they_hear_about_us                     varchar                                                  not null,
    details_on_how_they_heard_about_us             varchar                                                  not null,
    date_created                                   timestamp with time zone default now(),
    lead_salutation                                salutation_type          default ''::salutation_type     not null,
    appointment_date_and_time                      timestamp with time zone,
    send_confirmation_to_lead                      varchar(4)               default ''::character varying   not null,
    completed_appointment                          boolean                  default false                   not null,
    grade_level                                    grade_level_options      default ''::grade_level_options not null,
    recent_test_score                              integer                  default '-1'::integer           not null
);


