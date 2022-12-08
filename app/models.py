from app import db

class Transaction(db.Model):
    transaction_id = db.Column(db.String(8), primary_key=True, index=True, nullable=False, unique=True, default='')
    prospect_id = db.Column(db.String(8), db.ForeignKey('prospect.prospect_id'), index=True, nullable=False, default='')
    stripe_customer_id = db.Column(db.String(48),index=True,nullable=False, default='')
    salutation_type = db.Column(db.Enum('Mr.', 'Ms.', name='salutation'), index=True, nullable=False, default='')
    first_name = db.Column(db.String(64), index=True,nullable=False, default='')
    last_name = db.Column(db.String(64), index=True,nullable=False, default='')
    phone_number = db.Column(db.String(22),index=True,nullable=False, default='')
    email = db.Column(db.String(120), index=True,nullable=False, default='')
    was_diagnostic_purchased = db.Column(db.String(30), index=True, nullable=False, default='')
    diag_units = db.Column(db.Integer, index=True, nullable=False, default=-1)
    diag_total = db.Column(db.Integer, index=True, nullable=False, default=-1)
    was_test_prep_purchased = db.Column(db.String(30), index=True,nullable=False, default='')
    tp_product = db.Column(db.String(64), index=True,nullable=False, default='')
    tp_units = db.Column(db.Integer, index=True,nullable=False, default=-1)
    tp_total = db.Column(db.Integer, index=True,nullable=False, default=-1)
    was_college_apps_purchased = db.Column(db.String(30), index=True,nullable=False, default='')
    college_apps_product = db.Column(db.String(64), index=True,nullable=False, default='')
    college_apps_units = db.Column(db.Integer, index=True,nullable=False, default=-1)
    college_apps_total = db.Column(db.Integer, index=True,nullable=False, default=-1)
    adjust_total = db.Column(db.Float, index=True,nullable=False, default=-1)
    adjustment_explanation = db.Column(db.String(190), index=True, nullable=False, default='')
    transaction_total = db.Column(db.Integer, index=True, nullable=False, default=-1)
    installment_counter = db.Column(db.Integer, index=True, nullable=False, default=-1)
    date_created = db.Column(db.DateTime(timezone=True), index=True, server_default=db.func.now())
    payment_started = db.Column(db.Boolean, unique=False,nullable=False, default=False)
    amount_from_transaction_paid_so_far = db.Column(db.Integer, index=True, nullable=False, default=0)
    ask_for_student_info = db.Column(db.String(4), index=True,nullable=False, default='')
    does_customer_payment_info_exist = db.Column(db.String(30), index=True, nullable=False, default='')
    #installment_date = db.Column(db.PickleType,  index=True, nullable=True, default='')
    #installment_amount = db.Column(db.PickleType, index=True, nullable=True, default='')
    #what happens when you try to update pickle type? do you have to instantiate a new variable?


    def __repr__(self):
        return '<Transaction {}>'.format(self.transaction_id)


class InstallmentPlan(db.Model):
    transaction_id = db.Column(db.String(8), db.ForeignKey('transaction.transaction_id'), primary_key=True, nullable=False)
    stripe_customer_id = db.Column(db.String(48),index=True,nullable=False, default='')
    first_name = db.Column(db.String(64), index=True,nullable=False, default='')
    last_name = db.Column(db.String(64), index=True,nullable=False, default='')
    phone_number = db.Column(db.String(22),index=True,nullable=False, default='')
    email = db.Column(db.String(120), index=True,nullable=False, default='')

    date_1 = db.Column(db.Date,index=True,nullable=True)
    date_2 = db.Column(db.Date, index=True, nullable=True)
    date_3 = db.Column(db.Date, index=True, nullable=True)
    date_4 = db.Column(db.Date, index=True, nullable=True)
    date_5 = db.Column(db.Date, index=True, nullable=True)
    date_6 = db.Column(db.Date, index=True, nullable=True)
    date_7 = db.Column(db.Date, index=True, nullable=True)
    date_8 = db.Column(db.Date, index=True, nullable=True)
    date_9 = db.Column(db.Date, index=True, nullable=True)
    date_10 = db.Column(db.Date, index=True, nullable=True)
    date_11 = db.Column(db.Date, index=True, nullable=True)
    date_12 = db.Column(db.Date, index=True, nullable=True)

    amount_1 = db.Column(db.Integer, index=True,nullable=True, default=-1)
    amount_2 = db.Column(db.Integer, index=True, nullable=True, default=-1)
    amount_3 = db.Column(db.Integer, index=True, nullable=True, default=-1)
    amount_4 = db.Column(db.Integer, index=True, nullable=True, default=-1)
    amount_5 = db.Column(db.Integer, index=True, nullable=True, default=-1)
    amount_6 = db.Column(db.Integer, index=True, nullable=True, default=-1)
    amount_7 = db.Column(db.Integer, index=True,nullable=True, default=-1)
    amount_8 = db.Column(db.Integer, index=True, nullable=True, default=-1)
    amount_9 = db.Column(db.Integer, index=True, nullable=True, default=-1)
    amount_10 = db.Column(db.Integer, index=True, nullable=True, default=-1)
    amount_11 = db.Column(db.Integer, index=True,nullable=True, default=-1)
    amount_12 = db.Column(db.Integer, index=True,nullable=True, default=-1)


    def __repr__(self):
        return '<InstallmentPlan created for {}>'.format(self.transaction_id)

#invoices created for installments and for returning client autopay
class InvoiceToBePaid(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(8), db.ForeignKey('transaction.transaction_id'), nullable=False)
    stripe_customer_id = db.Column(db.String(48),index=True,nullable=False, default='')
    first_name = db.Column(db.String(64), index=True,nullable=False, default='')
    last_name = db.Column(db.String(64), index=True,nullable=False, default='')
    phone_number = db.Column(db.String(22),index=True,nullable=False, default='')
    email = db.Column(db.String(120), index=True,nullable=False, default='')

    payment_date = db.Column(db.Date, index=True, nullable=True)
    payment_amount = db.Column(db.Integer, index=True, nullable=True, default=-1)
    stripe_invoice_id = db.Column(db.String(64), index=True,nullable=False, default='')
    payment_made = db.Column(db.Boolean, unique=False, nullable=False, default=False)

    def __repr__(self):
        return '<InvoiceToBePaid created for {}>'.format(self.last_name)

class Prospect(db.Model):
    prospect_id = db.Column(db.String(8), unique=True, index=True, nullable=False, default='')
    prospect_first_name = db.Column(db.String(64), index=True,nullable=False, default='')
    prospect_last_name = db.Column(db.String(64), index=True,nullable=False, default='')
    prospect_email = db.Column(db.String(64), index=True, primary_key=True, nullable=False, default='')
    prospect_phone_number = db.Column(db.String(22),index=True,nullable=False, default='')
    how_did_they_hear_about_us = db.Column(db.String, index=True, nullable=False, default='')
    how_did_they_hear_about_us_details = db.Column(db.String, index=True, nullable=False, default='')
    #is_active = db.Column(db.Boolean, unique=False, nullable=False, server_default='True')
    #TODO add prospect salutation column

    def __repr__(self):
        return '<Prospect {} created with prospect_id {}>'.format(self.last_name, self.prospect_id)

class Lead(db.Model):
    lead_id = db.Column(db.String(8), primary_key=True, unique=True, index=True, nullable=False, default='')
    lead_name = db.Column(db.String(64), index=True,nullable=False, default='')
    lead_email = db.Column(db.String(64), index=True, nullable=False, default='')
    lead_phone_number = db.Column(db.String(22), index=True,nullable=False, default='')
    what_service_are_they_interested_in = db.Column(db.String, index=True, nullable=False, default='')
    what_next = db.Column(db.String, index=True, nullable=False, default='')
    meeting_notes_to_keep_in_mind = db.Column(db.String, index=True, nullable=False, default='')
    how_did_they_hear_about_us = db.Column(db.String, index=True, nullable=False, default='')
    how_did_they_hear_about_us_details = db.Column(db.String, index=True, nullable=False, default='')
    date_created = db.Column(db.DateTime(timezone=True), index=True, server_default=db.func.now())
    #is_active = db.Column(db.Boolean, unique=False, nullable=False, server_default='True')


    def __repr__(self):
        return '<Lead created with lead_id {}>'.format(self.lead_id)

class Student(db.Model):
    prospect_id = db.Column(db.String(8), db.ForeignKey('prospect.prospect_id'), index=True, nullable=False, default='')
    student_id = db.Column(db.String(8), unique=True, index=True, nullable=False, default='')
    student_first_name = db.Column(db.String(64), index=True, nullable=False, default='')
    student_last_name = db.Column(db.String(64), index=True, nullable=False, default='')
    student_email = db.Column(db.String(64), index=True,primary_key=True,unique=True,nullable=False, default='')
    student_phone_number = db.Column(db.String(22),index=True,nullable=False, default='')
    parent_1_salutation = db.Column(db.String(6), index=True, nullable=False, default='')
    parent_1_first_name = db.Column(db.String(64), index=True, nullable=False, default='')
    parent_1_last_name = db.Column(db.String(64), index=True, nullable=False, default='')
    parent_1_email = db.Column(db.String(64), index=True, nullable=False, default='')
    parent_1_phone_number = db.Column(db.String(22),index=True,nullable=False, default='')
    parent_2_salutation = db.Column(db.String(6), index=True, nullable=False, default='')
    parent_2_first_name = db.Column(db.String(64), index=True, nullable=False, default='')
    parent_2_last_name = db.Column(db.String(64), index=True, nullable=False, default='')
    parent_2_email = db.Column(db.String(64), index=True, nullable=False, default='')
    parent_2_phone_number = db.Column(db.String(22),index=True,nullable=False, default='')
    is_active = db.Column(db.Boolean, unique=False,nullable=False, server_default='True')


    def __repr__(self):
        return '<Student {} created with student_id {}>'.format(self.parent_1_last_name, self.student_id)


# class Test(db.Model):
#     student_id = db.Column(db.String(8), unique=True, index=True, nullable=False, default='')
#     student_first_name = db.Column(db.String(64), index=True, nullable=False, default='')
#     student_last_name = db.Column(db.String(64), index=True, nullable=False, default='')
#     student_email = db.Column(db.String(64), index=True,primary_key=True,unique=True,nullable=False, default='')
#     student_phone_number = db.Column(db.String(22),index=True,nullable=False, default='')
#     parent_1_salutation = db.Column(db.String(6), index=True, nullable=False, default='')
#     parent_1_first_name = db.Column(db.String(64), index=True, nullable=False, default='')
#     parent_1_last_name = db.Column(db.String(64), index=True, nullable=False, default='')
#     parent_1_email = db.Column(db.String(64), index=True, nullable=False, default='')
#     parent_1_phone_number = db.Column(db.String(22),index=True,nullable=False, default='')
#     parent_2_salutation = db.Column(db.String(6), index=True, nullable=False, default='')
#     parent_2_first_name = db.Column(db.String(64), index=True, nullable=False, default='')
#     parent_2_last_name = db.Column(db.String(64), index=True, nullable=False, default='')
#     parent_2_email = db.Column(db.String(64), index=True, nullable=False, default='')
#     parent_2_phone_number = db.Column(db.String(22),index=True,nullable=False, default='')
#     is_active = db.Column(db.Boolean, unique=False,nullable=False, server_default='True')
#
#
#     def __repr__(self):
#         return '<Student {} created with student_id {}>'.format(self.parent_1_last_name, self.student_id)


db.create_all()
try:
    db.session.commit()
except:
    # if any kind of exception occurs, rollback transaction
    db.session.rollback()
    raise
finally:
    db.session.close()

