from flask import Blueprint, render_template, jsonify, redirect, url_for, request, flash
from flask_login import login_required, current_user
import requests
from auth.models import Client, db
from auth.forms import ClientForm

web_bp = Blueprint('web', __name__, template_folder='templates')

@web_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')

@web_bp.route('/data')
@login_required
def get_data():
    """Get data for the dashboard"""
    # In a real app, this would fetch from a database
    # For now, get data from our test-audit endpoint
    response = requests.get(request.host_url + 'api/test-audit')
    return jsonify(response.json())

@web_bp.route('/clients')
@login_required
def client_list():
    clients = Client.query.filter_by(user_id=current_user.id).all()
    return render_template('clients/list.html', title='My Clients', clients=clients)

@web_bp.route('/clients/new', methods=['GET', 'POST'])
@login_required
def new_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            email=form.email.data,
            website=form.website.data,
            notes=form.notes.data,
            user_id=current_user.id
        )
        db.session.add(client)
        db.session.commit()
        flash('Client added successfully!', 'success')
        return redirect(url_for('web.client_list'))
    return render_template('clients/new.html', title='Add Client', form=form)

@web_bp.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    if client.user_id != current_user.id:
        flash('You do not have permission to edit this client.', 'danger')
        return redirect(url_for('web.client_list'))
    
    form = ClientForm()
    if form.validate_on_submit():
        client.name = form.name.data
        client.email = form.email.data
        client.website = form.website.data
        client.notes = form.notes.data
        db.session.commit()
        flash('Client updated successfully!', 'success')
        return redirect(url_for('web.client_list'))
    elif request.method == 'GET':
        form.name.data = client.name
        form.email.data = client.email
        form.website.data = client.website
        form.notes.data = client.notes
    
    return render_template('clients/edit.html', title='Edit Client', form=form, client=client)

@web_bp.route('/clients/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    if client.user_id != current_user.id:
        flash('You do not have permission to delete this client.', 'danger')
        return redirect(url_for('web.client_list'))
    
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully!', 'success')
    return redirect(url_for('web.client_list'))

@web_bp.route('/clients/<int:client_id>')
@login_required
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    if client.user_id != current_user.id:
        flash('You do not have permission to view this client.', 'danger')
        return redirect(url_for('web.client_list'))
    
    # In a real app, you would fetch the client's audit history here
    audits = []  # Replace with actual audit data
    
    return render_template('clients/detail.html', title=client.name, client=client, audits=audits)

@web_bp.route('/connect/facebook')
@login_required
def connect_facebook():
    """Facebook connection page"""
    return render_template('connections/facebook.html', title='Connect Facebook Ads')

@web_bp.route('/audit/facebook')
@login_required
def facebook_audit():
    """Facebook audit page"""
    # Get client ID from query string if available
    client_id = request.args.get('client_id')
    client = None

    if client_id:
        client = Client.query.get(client_id)
        if client and client.user_id != current_user.id:
            flash('You do not have permission to audit this client.', 'danger')
            return redirect(url_for('web.client_list'))

    # Get all clients for the dropdown
    clients = Client.query.filter_by(user_id=current_user.id).all()

    return render_template('audits/facebook.html', title='Facebook Ads Audit', 
                           client=client, clients=clients)