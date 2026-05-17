"""
DevFlow AI — Email Service
Uses Gmail SMTP (or any SMTP) to send real emails.

Setup:
  1. Enable 2-Factor Auth on your Gmail account
  2. Go to https://myaccount.google.com/apppasswords
  3. Create an App Password for "Mail"
  4. Put that 16-char password in .env as EMAIL_PASSWORD
"""

import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config.settings import settings

logger = logging.getLogger(__name__)


class EmailService:

    @staticmethod
    def _send(to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
        """Send a real email via SMTP. Returns True on success."""
        if not settings.EMAIL_HOST or not settings.EMAIL_USER or not settings.EMAIL_PASSWORD:
            logger.warning("Email not configured — skipping send. Set EMAIL_HOST, EMAIL_USER, EMAIL_PASSWORD in .env")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_USER}>"
            msg["To"]      = to_email

            # Plain text fallback
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))

            # HTML version
            msg.attach(MIMEText(html_body, "html"))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, context=context) as server:
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.sendmail(settings.EMAIL_USER, to_email, msg.as_string())

            logger.info(f"✅ Email sent to {to_email}: {subject}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Email auth failed. Check EMAIL_USER and EMAIL_PASSWORD in .env")
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error sending to {to_email}: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {e}")

        return False

    # ─── WELCOME EMAIL ───
    @staticmethod
    def send_welcome(to_email: str, name: str) -> bool:
        subject = "Welcome to DevFlow AI 🚀"
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#0d1117;font-family:'Segoe UI',sans-serif;">
          <div style="max-width:560px;margin:40px auto;background:#161b27;border-radius:16px;overflow:hidden;border:1px solid #21262d;">

            <!-- Header -->
            <div style="background:linear-gradient(135deg,#0fb6ff,#0f62fe);padding:40px 40px 30px;">
              <div style="width:48px;height:48px;background:rgba(255,255,255,0.2);border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;color:#fff;margin-bottom:16px;">DF</div>
              <h1 style="margin:0;color:#fff;font-size:26px;font-weight:700;">Welcome to DevFlow AI!</h1>
              <p style="margin:8px 0 0;color:rgba(255,255,255,0.8);font-size:15px;">Your AI-powered developer platform is ready.</p>
            </div>

            <!-- Body -->
            <div style="padding:36px 40px;">
              <p style="color:#c9d1d9;font-size:16px;margin:0 0 20px;">Hi <strong style="color:#fff;">{name}</strong>,</p>
              <p style="color:#8b949e;font-size:15px;line-height:1.6;margin:0 0 28px;">
                You're all set! DevFlow AI is your IBM BOB-powered platform to analyze, document, and improve your code — in under 60 seconds.
              </p>

              <!-- Features -->
              <div style="background:#0d1117;border-radius:10px;padding:20px 24px;margin-bottom:28px;">
                <p style="color:#fff;font-weight:600;margin:0 0 12px;font-size:14px;">✨ What you can do:</p>
                <p style="color:#8b949e;font-size:14px;margin:6px 0;">🤖 <strong style="color:#c9d1d9;">AI Code Analysis</strong> — Understand any repo instantly</p>
                <p style="color:#8b949e;font-size:14px;margin:6px 0;">📋 <strong style="color:#c9d1d9;">Project Management</strong> — Tasks, teams, deployments</p>
                <p style="color:#8b949e;font-size:14px;margin:6px 0;">📊 <strong style="color:#c9d1d9;">Analytics</strong> — Real-time dev metrics</p>
                <p style="color:#8b949e;font-size:14px;margin:6px 0;">⚡ <strong style="color:#c9d1d9;">IBM watsonx</strong> — Enterprise AI under the hood</p>
              </div>

              <!-- CTA Button -->
              <div style="text-align:center;margin-bottom:28px;">
                <a href="{settings.FRONTEND_URL}" style="display:inline-block;background:linear-gradient(135deg,#0fb6ff,#0f62fe);color:#fff;text-decoration:none;padding:14px 36px;border-radius:10px;font-weight:600;font-size:15px;">
                  Open DevFlow AI →
                </a>
              </div>

              <p style="color:#8b949e;font-size:13px;text-align:center;margin:0;">
                Questions? Just reply to this email.<br>
                Built with ❤️ for IBM BOB Hackathon
              </p>
            </div>

            <!-- Footer -->
            <div style="border-top:1px solid #21262d;padding:20px 40px;text-align:center;">
              <p style="color:#484f58;font-size:12px;margin:0;">
                DevFlow AI · You're receiving this because you signed up at DevFlow AI
              </p>
            </div>
          </div>
        </body>
        </html>
        """
        text = f"Welcome to DevFlow AI, {name}!\n\nYour account is ready. Visit: {settings.FRONTEND_URL}"
        return EmailService._send(to_email, subject, html, text)

    # ─── PASSWORD RESET EMAIL ───
    @staticmethod
    def send_password_reset(to_email: str, name: str, reset_token: str) -> bool:
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Reset Your DevFlow AI Password"
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#0d1117;font-family:'Segoe UI',sans-serif;">
          <div style="max-width:560px;margin:40px auto;background:#161b27;border-radius:16px;overflow:hidden;border:1px solid #21262d;">

            <div style="background:linear-gradient(135deg,#f59e0b,#ef4444);padding:40px 40px 30px;">
              <h1 style="margin:0;color:#fff;font-size:24px;font-weight:700;">Password Reset Request</h1>
              <p style="margin:8px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">Someone requested a password reset for your account.</p>
            </div>

            <div style="padding:36px 40px;">
              <p style="color:#c9d1d9;font-size:16px;margin:0 0 16px;">Hi <strong style="color:#fff;">{name}</strong>,</p>
              <p style="color:#8b949e;font-size:15px;line-height:1.6;margin:0 0 28px;">
                Click the button below to reset your password. This link expires in <strong style="color:#f59e0b;">30 minutes</strong>.
              </p>

              <div style="text-align:center;margin-bottom:28px;">
                <a href="{reset_link}" style="display:inline-block;background:linear-gradient(135deg,#f59e0b,#ef4444);color:#fff;text-decoration:none;padding:14px 36px;border-radius:10px;font-weight:600;font-size:15px;">
                  Reset My Password
                </a>
              </div>

              <div style="background:#0d1117;border-radius:10px;padding:16px 20px;margin-bottom:20px;">
                <p style="color:#484f58;font-size:12px;margin:0 0 6px;">Or copy this link:</p>
                <p style="color:#0fb6ff;font-size:12px;word-break:break-all;margin:0;">{reset_link}</p>
              </div>

              <p style="color:#484f58;font-size:13px;margin:0;">
                ⚠️ If you didn't request this, you can safely ignore this email. Your password won't change.
              </p>
            </div>

            <div style="border-top:1px solid #21262d;padding:20px 40px;text-align:center;">
              <p style="color:#484f58;font-size:12px;margin:0;">DevFlow AI — Security Team</p>
            </div>
          </div>
        </body>
        </html>
        """
        text = f"Hi {name},\n\nReset your DevFlow AI password here:\n{reset_link}\n\nThis link expires in 30 minutes.\n\nIf you didn't request this, ignore this email."
        return EmailService._send(to_email, subject, html, text)

    # ─── LOGIN ALERT EMAIL ───
    @staticmethod
    def send_login_alert(to_email: str, name: str, ip: str = "Unknown") -> bool:
        subject = "New Login to DevFlow AI"
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#0d1117;font-family:'Segoe UI',sans-serif;">
          <div style="max-width:560px;margin:40px auto;background:#161b27;border-radius:16px;overflow:hidden;border:1px solid #21262d;">

            <div style="background:linear-gradient(135deg,#0fb6ff,#22c55e);padding:32px 40px;">
              <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700;">✅ New Login Detected</h1>
            </div>

            <div style="padding:36px 40px;">
              <p style="color:#c9d1d9;font-size:15px;margin:0 0 20px;">Hi <strong style="color:#fff;">{name}</strong>, a new login was recorded on your account.</p>

              <div style="background:#0d1117;border-radius:10px;padding:20px 24px;margin-bottom:24px;">
                <p style="color:#8b949e;font-size:14px;margin:0 0 8px;">📍 IP Address: <strong style="color:#c9d1d9;">{ip}</strong></p>
                <p style="color:#8b949e;font-size:14px;margin:0;">⏰ Time: <strong style="color:#c9d1d9;">Just now</strong></p>
              </div>

              <p style="color:#484f58;font-size:13px;margin:0;">
                If this wasn't you, please reset your password immediately.
              </p>
            </div>

            <div style="border-top:1px solid #21262d;padding:20px 40px;text-align:center;">
              <p style="color:#484f58;font-size:12px;margin:0;">DevFlow AI Security</p>
            </div>
          </div>
        </body>
        </html>
        """
        text = f"New login to your DevFlow AI account from IP: {ip}. If this wasn't you, reset your password."
        return EmailService._send(to_email, subject, html, text)

    # ─── EMAIL VERIFICATION ───
    @staticmethod
    def send_verification(to_email: str, name: str, verification_token: str) -> bool:
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        subject = "Verify Your DevFlow AI Email"
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#0d1117;font-family:'Segoe UI',sans-serif;">
          <div style="max-width:560px;margin:40px auto;background:#161b27;border-radius:16px;overflow:hidden;border:1px solid #21262d;">

            <div style="background:linear-gradient(135deg,#0fb6ff,#0f62fe);padding:40px 40px 30px;">
              <h1 style="margin:0;color:#fff;font-size:24px;font-weight:700;">Verify Your Email</h1>
              <p style="margin:8px 0 0;color:rgba(255,255,255,0.85);font-size:14px;">One more step to activate your account.</p>
            </div>

            <div style="padding:36px 40px;">
              <p style="color:#c9d1d9;font-size:16px;margin:0 0 16px;">Hi <strong style="color:#fff;">{name}</strong>,</p>
              <p style="color:#8b949e;font-size:15px;line-height:1.6;margin:0 0 28px;">
                Click the button below to verify your email and get full access to DevFlow AI. This link expires in <strong style="color:#0fb6ff;">24 hours</strong>.
              </p>

              <div style="text-align:center;margin-bottom:28px;">
                <a href="{verification_link}" style="display:inline-block;background:linear-gradient(135deg,#0fb6ff,#0f62fe);color:#fff;text-decoration:none;padding:14px 36px;border-radius:10px;font-weight:600;font-size:15px;">
                  Verify My Email
                </a>
              </div>

              <div style="background:#0d1117;border-radius:10px;padding:16px 20px;margin-bottom:20px;">
                <p style="color:#484f58;font-size:12px;margin:0 0 6px;">Or copy this link:</p>
                <p style="color:#0fb6ff;font-size:12px;word-break:break-all;margin:0;">{verification_link}</p>
              </div>

              <p style="color:#484f58;font-size:13px;margin:0;">
                ⚠️ If you didn't create this account, you can safely ignore this email.
              </p>
            </div>

            <div style="border-top:1px solid #21262d;padding:20px 40px;text-align:center;">
              <p style="color:#484f58;font-size:12px;margin:0;">DevFlow AI — Verification Team</p>
            </div>
          </div>
        </body>
        </html>
        """
        text = f"Hi {name},\n\nVerify your DevFlow AI email here:\n{verification_link}\n\nThis link expires in 24 hours.\n\nIf you didn't create this account, ignore this email."
        return EmailService._send(to_email, subject, html, text)


# Singleton
email_service = EmailService()
