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


alter table lead drop COLUMN completed_appointment;
alter table lead add column appointment_completed varchar(4) NOT NULL CONSTRAINT appointment_completed_constraint DEFAULT('');
alter table transaction add column ask_for_student_availability varchar(4) NOT NULL CONSTRAINT ask_for_student_availability_constraint DEFAULT('');


alter table invoice_to_be_paid drop column date_created;
alter table invoice_to_be_paid ADD COLUMN date_created TIMESTAMP WITH TIME ZONE  ;
ALTER TABLE invoice_to_be_paid ALTER COLUMN date_created SET DEFAULT now();


ALTER TABLE transaction ALTER COLUMN date_created SET DEFAULT now();
ALTER TABLE installment_plan ALTER COLUMN date_created SET DEFAULT now();
ALTER TABLE invoice_to_be_paid ALTER COLUMN date_created SET DEFAULT now();
ALTER TABLE prospect ALTER COLUMN date_created SET DEFAULT now();
ALTER TABLE lead ALTER COLUMN date_created SET DEFAULT now();
alter table student ADD COLUMN date_created TIMESTAMP WITH TIME ZONE  ;
ALTER TABLE student ALTER COLUMN date_created SET DEFAULT now();

