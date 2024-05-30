from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user
from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import select
from sqlalchemy.orm import with_parent
from werkzeug.wrappers.response import Response

from ..core.extensions import db
from ..emails import (
    send_new_comment_email,
    send_new_reply_email,
)
from ..forms import (
    AdminCommentForm,
    CommentForm,
)
from ..models import (
    Category,
    Comment,
    Link,
    Post,
)
from ..utils import redirect_back

bp_blog = Blueprint('blog', __name__)


@bp_blog.route('/')
def index() -> str:
    page: int = request.args.get('page', 1, type=int)
    per_page: int = current_app.config['GREYBOOK_POSTS_PER_PAGE']
    pagination: Pagination = db.paginate(
        select(Post).order_by(Post.created_time.desc()),
        page=page,
        per_page=per_page,
    )
    posts: list[Post] = pagination.items
    return render_template('blog/index.html', pagination=pagination, posts=posts)


@bp_blog.route('/about')
def about():
    return render_template('blog/about.html')


@bp_blog.route('/category/<int:category_id>')
def show_category(category_id: int) -> str:
    category: Category = db.get_or_404(Category, category_id)
    page: int = request.args.get('page', 1, type=int)
    per_page: int = current_app.config['GREYBOOK_POST_PER_PAGE']
    pagination: Pagination = db.paginate(
        select(Post).filter(with_parent(category, Category.posts)).order_by(Post.created_time.desc()),
        page=page,
        per_page=per_page,
    )
    posts: list[Post] = pagination.items
    return render_template('blog/category.html', category=category, pagination=pagination, posts=posts)


@bp_blog.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id: int) -> Response | str:
    post: Post = db.get_or_404(Post, post_id)

    from_admin: bool = current_user.is_authenticated
    if from_admin:
        form = AdminCommentForm()
        form.admin_init()
    else:
        form = CommentForm()

    if form.validate_on_submit():
        comment: Comment = Comment.from_form(form, from_admin=from_admin, post_id=post_id)
        replied_id: str | None = request.args.get('reply')
        if replied_id:
            replied_comment: Comment = db.get_or_404(Comment, replied_id)
            comment.replied = replied_comment
            send_new_reply_email(replied_comment)
        db.session.add(comment)
        db.session.commit()
        if current_user.is_authenticated:  # send message based on authentication status
            flash('Comment published.', 'success')
        else:
            flash('Thanks, your comment will be published after reviewed.', 'info')
            send_new_comment_email(post)  # send notification email to admin
        return redirect(url_for('.show_post', post_id=post_id))

    page: int = request.args.get('page', 1, type=int)
    per_page: int = current_app.config['GREYBOOK_COMMENT_PER_PAGE']
    pagination: Pagination = db.paginate(
        select(Comment).filter(with_parent(post, Post.comments)).filter_by(reviewed=True).order_by(Comment.created_time.asc()),
        page=page,
        per_page=per_page,
    )
    comments: list[Comment] = pagination.items

    return render_template('blog/post.html', post=post, pagination=pagination, form=form, comments=comments)


@bp_blog.route('/reply/comment/<int:comment_id>')
def reply_comment(comment_id: int) -> Response:
    comment: Comment = db.get_or_404(Comment, comment_id)
    if comment.post.no_comment:
        flash('Comment is disabled.', 'warning')
        return redirect(url_for('.show_post', post_id=comment.post.id))

    return redirect(
        url_for(
            '.show_post',
            post_id=comment.post_id,
            reply=comment_id,
            author=comment.author,
        )
        + '#comment-form'
    )


@bp_blog.route('/change-theme/<theme_name>')
def change_theme(theme_name: str) -> Response:
    if theme_name not in current_app.config['GREYBOOK_THEMES']:
        abort(400, description='Invalid theme name.')

    response: Response = make_response(redirect_back())
    response.set_cookie('theme', theme_name, max_age=30 * 24 * 60 * 60)
    return response


@bp_blog.route('/uploads/<path:filename>')
def get_image(filename) -> Response:
    return send_from_directory(current_app.config['GREYBOOK_UPLOAD_PATH'], filename)
