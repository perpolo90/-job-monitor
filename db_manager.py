#!/usr/bin/env python3
"""
Database Manager for Job Monitor
Simple script to view and manage job database entries.
"""

import sqlite3
import argparse
from datetime import datetime

def view_jobs(status=None, limit=50):
    """View jobs from the database."""
    with sqlite3.connect('jobs.db') as conn:
        cursor = conn.cursor()
        
        if status:
            cursor.execute('''
                SELECT id, title, company, location, status, first_seen, last_updated
                FROM jobs WHERE status = ? ORDER BY last_updated DESC LIMIT ?
            ''', (status, limit))
        else:
            cursor.execute('''
                SELECT id, title, company, location, status, first_seen, last_updated
                FROM jobs ORDER BY last_updated DESC LIMIT ?
            ''', (limit,))
        
        jobs = cursor.fetchall()
        
        if not jobs:
            print(f"No jobs found{' with status: ' + status if status else ''}")
            return
        
        print(f"\nFound {len(jobs)} jobs{' with status: ' + status if status else ''}:")
        print("-" * 100)
        print(f"{'ID':<4} {'Title':<40} {'Company':<20} {'Status':<10} {'First Seen':<20}")
        print("-" * 100)
        
        for job in jobs:
            id, title, company, location, status, first_seen, last_updated = job
            title_short = title[:37] + "..." if len(title) > 40 else title
            print(f"{id:<4} {title_short:<40} {company:<20} {status:<10} {first_seen[:19]:<20}")

def update_job_status(job_id, new_status, notes=None):
    """Update job status."""
    with sqlite3.connect('jobs.db') as conn:
        cursor = conn.cursor()
        
        # Get job hash
        cursor.execute('SELECT job_hash FROM jobs WHERE id = ?', (job_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"Job with ID {job_id} not found")
            return
        
        job_hash = result[0]
        
        # Update status in jobs table
        cursor.execute('''
            UPDATE jobs SET status = ?, last_updated = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (new_status, job_id))
        
        # Add to history
        cursor.execute('''
            INSERT INTO job_status_history (job_hash, status, notes)
            VALUES (?, ?, ?)
        ''', (job_hash, new_status, notes or f"Status updated to {new_status}"))
        
        conn.commit()
        print(f"Updated job {job_id} status to: {new_status}")

def view_job_details(job_id):
    """View detailed information about a specific job."""
    with sqlite3.connect('jobs.db') as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, company, url, location, department, employment_type, 
                   status, first_seen, last_updated, notes
            FROM jobs WHERE id = ?
        ''', (job_id,))
        
        job = cursor.fetchone()
        if not job:
            print(f"Job with ID {job_id} not found")
            return
        
        title, company, url, location, department, employment_type, status, first_seen, last_updated, notes = job
        
        print(f"\nJob Details (ID: {job_id}):")
        print("=" * 50)
        print(f"Title: {title}")
        print(f"Company: {company}")
        print(f"URL: {url}")
        print(f"Location: {location or 'Not specified'}")
        print(f"Department: {department or 'Not specified'}")
        print(f"Employment Type: {employment_type or 'Not specified'}")
        print(f"Status: {status}")
        print(f"First Seen: {first_seen}")
        print(f"Last Updated: {last_updated}")
        print(f"Notes: {notes or 'None'}")
        
        # Show status history
        cursor.execute('''
            SELECT status, timestamp, notes
            FROM job_status_history 
            WHERE job_hash = (SELECT job_hash FROM jobs WHERE id = ?)
            ORDER BY timestamp DESC
        ''', (job_id,))
        
        history = cursor.fetchall()
        if history:
            print(f"\nStatus History:")
            print("-" * 50)
            for status, timestamp, notes in history:
                print(f"{timestamp[:19]} - {status}: {notes}")

def view_status_summary():
    """View summary of jobs by status."""
    with sqlite3.connect('jobs.db') as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM jobs 
            GROUP BY status 
            ORDER BY count DESC
        ''')
        
        results = cursor.fetchall()
        
        if not results:
            print("No jobs found in database")
            return
        
        print("\nJob Status Summary:")
        print("=" * 30)
        for status, count in results:
            print(f"{status}: {count} jobs")

def main():
    parser = argparse.ArgumentParser(description='Job Monitor Database Manager')
    parser.add_argument('action', choices=['view', 'update', 'details', 'summary'],
                       help='Action to perform')
    parser.add_argument('--status', help='Filter by status (for view action)')
    parser.add_argument('--limit', type=int, default=50, help='Limit number of results (default: 50)')
    parser.add_argument('--id', type=int, help='Job ID (for update and details actions)')
    parser.add_argument('--new-status', help='New status (for update action)')
    parser.add_argument('--notes', help='Notes for status update (for update action)')
    
    args = parser.parse_args()
    
    if args.action == 'view':
        view_jobs(args.status, args.limit)
    elif args.action == 'update':
        if not args.id or not args.new_status:
            print("Error: --id and --new-status are required for update action")
            return
        update_job_status(args.id, args.new_status, args.notes)
    elif args.action == 'details':
        if not args.id:
            print("Error: --id is required for details action")
            return
        view_job_details(args.id)
    elif args.action == 'summary':
        view_status_summary()

if __name__ == "__main__":
    main()
