from app import db

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_code = db.Column(db.String(8),index=True,nullable=False, default='')
    stripe_customer_id = db.Column(db.String(48),index=True,nullable=False, default='')
    first_name = db.Column(db.String(64), index=True,nullable=False, default='')
    last_name = db.Column(db.String(64), index=True,nullable=False, default='')
    phone_number = db.Column(db.String(12),index=True,nullable=False, default='')
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
    turn_on_installments = db.Column(db.Boolean, unique=False, default=False)
    installment_date_1 = db.Column(db.Date,index=True,nullable=True,default='')
    installment_date_2 = db.Column(db.Date, index=True, nullable=True, default='')
    installment_date_3 = db.Column(db.Date, index=True, nullable=True, default='')
    adjust_total = db.Column(db.Integer, index=True,nullable=False, default=-1)
    adjustment_explanation = db.Column(db.String(90), index=True, nullable=False, default='')
    invoice_total = db.Column(db.Integer, index=True,nullable=False, default=-1)
    date_created = db.Column(db.DateTime(timezone=True), index=True, server_default=db.func.now())
    payment_started = db.Column(db.Boolean, unique=False,nullable=False, default=False)
    amount_from_invoice_paid_so_far = db.Column(db.Integer, index=True, nullable=False, default=0)

    def __repr__(self):
        return '<Client {}>'.format(self.invoice_code)

db.create_all()
try:
    db.session.commit()
except:
    # if any kind of exception occurs, rollback transaction
    db.session.rollback()
    raise
finally:
    db.session.close()

