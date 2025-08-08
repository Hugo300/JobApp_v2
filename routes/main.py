from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
import os
from pathlib import Path

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    """Dashboard showing all job applications"""
    from models import JobApplication
    jobs = JobApplication.query.order_by(JobApplication.last_update.desc()).all()
    return render_template('dashboard.html', jobs=jobs)

@main_bp.route('/user', methods=['GET', 'POST'])
def user_data():
    """Manage user data"""
    from models import UserData
    user_data = UserData.query.first()
    
    if request.method == 'POST':
        if user_data is None:
            user_data = UserData()
            db.session.add(user_data)
        
        user_data.name = request.form['name']
        user_data.email = request.form['email']
        user_data.phone = request.form['phone']
        user_data.linkedin = request.form['linkedin']
        user_data.github = request.form['github']
        user_data.skills = request.form['skills']
        
        db.session.commit()
        flash('User data updated successfully!', 'success')
        return redirect(url_for('main.user_data'))
    
    return render_template('user_data.html', user_data=user_data)