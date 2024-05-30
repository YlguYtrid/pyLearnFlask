from threading import Thread

from flask import (
    Flask,
    current_app,
    url_for,
)
from flask_mailman import EmailMessage

from .models import (
    Comment,
    Post,
)


def _send_async_mail(app: Flask, message: EmailMessage) -> None:
    """
    Tread target function to send email asynchronously.

    Parameters
    ----------
    app : Flask
        Flask application instance.
    message : EmailMessage
        Email message to be sent.
    """
    with app.app_context():
        message.send()


def send_mail(subject: str, body: str, to: str) -> None | Thread:
    """
    Send email asynchronously using a thread.

    Parameters
    ----------
    subject : str
        Email subject.
    body : str
        Email body.
    to : str
        Email recipient.

    Returns
    -------
    None | Thread
        Thread object if current_app.debug is False, otherwise None.
    """
    if current_app.debug:
        current_app.logger.debug('Skip sending email in debug mode.')
        current_app.logger.debug(f'To: {to}')  # noqa: G004
        current_app.logger.debug(f'Subject: {subject}')  # noqa: G004
        current_app.logger.debug(f'Body: {body}')  # noqa: G004
        return
    app: Flask = current_app._get_current_object()  # type: ignore
    message = EmailMessage(subject, body=body, to=(to,))
    message.content_subtype = 'html'
    thr = Thread(target=_send_async_mail, args=(app, message))
    thr.start()
    return thr


def send_new_comment_email(post: Post) -> None:
    """
    Send email to admin when a new comment is added to a post.

    Parameters
    ----------
    post : Post
        Post instance.
    """
    post_url: str = url_for('blog.show_post', post_id=post.id, _external=True) + '#comments'
    send_mail(
        subject='New comment',
        body=f'<p>New comment in post <i>{post.title}</i>, click the link below to check:</p> <p><a href="{post_url}">{post_url}</a></p> <p><small style="color: #868e96">Do not reply this email.</small></p>',
        to=current_app.config['GREYBOOK_ADMIN_EMAIL'],
    )


def send_new_reply_email(comment: Comment) -> None:
    """
    Send email to the user who left the comment when a new reply is added to it.

    Parameters
    ----------
    comment : Comment
        Comment instance.
    """
    post_url: str = url_for('blog.show_post', post_id=comment.post_id, _external=True) + '#comments'
    send_mail(
        subject='New reply',
        body=f'<p>New reply for the comment you left in post <i>{comment.post.title}</i>, click the link below to check: </p><p><a href="{post_url}">{post_url}</a></p> <p><small style="color: #868e96">Do not reply this email.</small></p>',
        to=comment.email,  # type: ignore
    )
