"""
Email Reporter
Generates and sends reports about driver management operations
"""

import logging
from typing import Dict, List
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Try to import win32com for Outlook integration
try:
    import win32com.client
    OUTLOOK_AVAILABLE = True
except ImportError:
    OUTLOOK_AVAILABLE = False
    logging.warning("pywin32 not installed - Outlook integration unavailable")

from jinja2 import Template

logger = logging.getLogger(__name__)


class EmailReporter:
    """Generates and sends email reports for driver operations"""
    
    def __init__(self, config: Dict[str, any], use_outlook: bool = False):
        """
        Initialize Email Reporter
        
        Args:
            config: Email configuration dictionary containing:
                - smtp_server: SMTP server address
                - smtp_port: SMTP port
                - smtp_username: SMTP username (optional)
                - smtp_password: SMTP password (optional)
                - from_email: Sender email address
                - to_emails: List of recipient email addresses
                - use_tls: Whether to use TLS (default: True)
            use_outlook: Whether to use Outlook COM instead of SMTP
        """
        self.config = config
        self.use_outlook = use_outlook and OUTLOOK_AVAILABLE
        
        if self.use_outlook:
            logger.info("Using Outlook COM for email sending")
        else:
            logger.info("Using SMTP for email sending")
    
    def send_operations_report(self, operations_log: Dict[str, List], 
                             summary_stats: Dict[str, int]) -> bool:
        """
        Send email report of driver operations
        
        Args:
            operations_log: Dictionary with created, updated, deactivated, and errors
            summary_stats: Summary statistics
            
        Returns:
            True if email sent successfully
        """
        subject = f"Samsara Driver Operations Report - {datetime.now().strftime('%Y-%m-%d')}"
        html_body = self._generate_html_report(operations_log, summary_stats)
        
        try:
            if self.use_outlook:
                return self._send_via_outlook(subject, html_body)
            else:
                return self._send_via_smtp(subject, html_body)
        except Exception as e:
            logger.error(f"Failed to send email report: {e}")
            return False
    
    def _generate_html_report(self, operations_log: Dict[str, List], 
                            summary_stats: Dict[str, int]) -> str:
        """Generate HTML email report"""
        
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
        .summary { background-color: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .summary-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .stat-box { background-color: white; padding: 10px; border-radius: 3px; text-align: center; }
        .stat-number { font-size: 24px; font-weight: bold; color: #3498db; }
        .section { margin: 20px 0; }
        .section-title { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
        table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .success { color: #27ae60; }
        .error { color: #e74c3c; }
        .warning { color: #f39c12; }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Samsara Driver Operations Report</h1>
        <p>{{ report_date }}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <div class="summary-grid">
            <div class="stat-box">
                <div class="stat-number success">{{ stats.drivers_created }}</div>
                <div>Drivers Created</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ stats.drivers_updated }}</div>
                <div>Drivers Updated</div>
            </div>
            <div class="stat-box">
                <div class="stat-number warning">{{ stats.drivers_deactivated }}</div>
                <div>Drivers Deactivated</div>
            </div>
            <div class="stat-box">
                <div class="stat-number error">{{ stats.errors }}</div>
                <div>Errors</div>
            </div>
        </div>
    </div>
    
    {% if operations.created %}
    <div class="section">
        <h2 class="section-title">New Drivers Created</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Driver ID</th>
                <th>Payroll ID</th>
                <th>Time</th>
            </tr>
            {% for driver in operations.created %}
            <tr>
                <td>{{ driver.name }}</td>
                <td>{{ driver.driver_id }}</td>
                <td>{{ driver.payroll_id or 'N/A' }}</td>
                <td>{{ driver.timestamp | format_time }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}
    
    {% if operations.updated %}
    <div class="section">
        <h2 class="section-title">Drivers Updated</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Driver ID</th>
                <th>Payroll ID</th>
                <th>Fields Updated</th>
                <th>Time</th>
            </tr>
            {% for driver in operations.updated %}
            <tr>
                <td>{{ driver.name }}</td>
                <td>{{ driver.driver_id }}</td>
                <td>{{ driver.payroll_id or 'N/A' }}</td>
                <td>{{ driver.fields_updated | join(', ') }}</td>
                <td>{{ driver.timestamp | format_time }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}
    
    {% if operations.deactivated %}
    <div class="section">
        <h2 class="section-title">Drivers Deactivated</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Driver ID</th>
                <th>Payroll ID</th>
                <th>Reason</th>
                <th>Time</th>
            </tr>
            {% for driver in operations.deactivated %}
            <tr>
                <td>{{ driver.name }}</td>
                <td>{{ driver.driver_id }}</td>
                <td>{{ driver.payroll_id or 'N/A' }}</td>
                <td>{{ driver.reason }}</td>
                <td>{{ driver.timestamp | format_time }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}
    
    {% if operations.errors %}
    <div class="section">
        <h2 class="section-title error">Errors</h2>
        <table>
            <tr>
                <th>Error</th>
                <th>Details</th>
                <th>Time</th>
            </tr>
            {% for error in operations.errors %}
            <tr>
                <td class="error">{{ error.error }}</td>
                <td>{{ error.row | format_row if error.row else error.payroll_id or 'N/A' }}</td>
                <td>{{ error.timestamp | format_time }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}
    
    <div class="footer">
        <p>This is an automated report from the Samsara Fleet Management System</p>
        <p>Generated on {{ report_date }} at {{ report_time }}</p>
    </div>
</body>
</html>
        """)
        
        # Custom filters
        def format_time(timestamp):
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d %H:%M')
            except Exception:
                return timestamp
        
        def format_row(row):
            if isinstance(row, dict):
                return f"{row.get('name', 'Unknown')} ({row.get('payroll_id', 'N/A')})"
            return str(row)
        
        template.filters['format_time'] = format_time
        template.filters['format_row'] = format_row
        
        # Render template
        html = template.render(
            operations=operations_log,
            stats=summary_stats,
            report_date=datetime.now().strftime('%B %d, %Y'),
            report_time=datetime.now().strftime('%I:%M %p')
        )
        
        return html
    
    def _send_via_smtp(self, subject: str, html_body: str) -> bool:
        """Send email via SMTP"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.config['from_email']
        msg['To'] = ', '.join(self.config['to_emails'])
        
        # Create plain text version
        text_body = self._html_to_text(html_body)
        
        # Attach parts
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        try:
            # Connect to server
            server = smtplib.SMTP(self.config['smtp_server'], self.config.get('smtp_port', 587))
            
            if self.config.get('use_tls', True):
                server.starttls()
            
            # Login if credentials provided
            if self.config.get('smtp_username') and self.config.get('smtp_password'):
                server.login(self.config['smtp_username'], self.config['smtp_password'])
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {msg['To']}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise
    
    def _send_via_outlook(self, subject: str, html_body: str) -> bool:
        """Send email via Outlook COM automation"""
        try:
            outlook = win32com.client.Dispatch('Outlook.Application')
            mail = outlook.CreateItem(0)  # 0 = Mail item
            
            mail.Subject = subject
            mail.HTMLBody = html_body
            mail.To = '; '.join(self.config['to_emails'])
            
            # Optional: Add CC recipients
            if self.config.get('cc_emails'):
                mail.CC = '; '.join(self.config['cc_emails'])
            
            mail.Send()
            
            logger.info(f"Email sent successfully via Outlook to {mail.To}")
            return True
            
        except Exception as e:
            logger.error(f"Outlook error: {e}")
            raise
    
    def _html_to_text(self, html: str) -> str:
        """Simple HTML to text conversion"""
        # This is a basic implementation - could be improved with BeautifulSoup
        import re
        
        # Remove style tags
        text = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL)
        # Remove script tags
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()


# Test email functionality
if __name__ == "__main__":
    # Example configuration for testing
    email_config = {
        'smtp_server': 'smtp.office365.com',
        'smtp_port': 587,
        'smtp_username': 'your_email@company.com',
        'smtp_password': 'your_password',
        'from_email': 'your_email@company.com',
        'to_emails': ['recipient@company.com'],
        'use_tls': True
    }
    
    # Example data
    test_operations = {
        'created': [
            {
                'driver_id': '123',
                'name': 'John Smith',
                'payroll_id': 'EMP001',
                'timestamp': datetime.utcnow().isoformat()
            }
        ],
        'updated': [],
        'deactivated': [],
        'errors': []
    }
    
    test_stats = {
        'drivers_created': 1,
        'drivers_updated': 0,
        'drivers_deactivated': 0,
        'errors': 0
    }
    
    # Send test email
    # reporter = EmailReporter(email_config, use_outlook=True)
    # reporter.send_operations_report(test_operations, test_stats)