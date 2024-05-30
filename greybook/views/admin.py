import os

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_ckeditor import (
    upload_fail,
    upload_success,
)
from flask_login import (
    current_user,
    login_required,
)
from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import (
    Select,
    select,
)
from werkzeug.datastructures.file_storage import FileStorage
from werkzeug.wrappers.response import Response

from ..core.extensions import db
from ..forms import (
    CategoryForm,
    LinkForm,
    PostForm,
    SettingForm,
)
from ..models import (
    Category,
    Comment,
    Link,
    Post,
)
from ..utils import (
    allowed_file,
    random_filename,
    redirect_back,
)

bp_admin = Blueprint('admin', __name__)


@bp_admin.before_request
@login_required
def login_protect() -> None:
    """
    Before request function to check if user is admin.
    """
    pass


# settings start
@bp_admin.route('/settings', methods=['GET', 'POST'])
def settings() -> Response | str:
    form = SettingForm()
    match request.method:
        case 'GET':
            form.name.data = current_user.name
            form.blog_title.data = current_user.blog_title
            form.blog_sub_title.data = current_user.blog_sub_title
            form.about.data = current_user.about
            form.custom_footer.data = current_user.custom_footer
            form.custom_css.data = current_user.custom_css
            form.custom_js.data = current_user.custom_js
        case 'POST':
            if form.validate_on_submit():
                current_user.name = form.name.data
                current_user.blog_title = form.blog_title.data
                current_user.blog_sub_title = form.blog_sub_title.data
                current_user.about = form.about.data
                current_user.custom_footer = form.custom_footer.data
                current_user.custom_css = form.custom_css.data
                current_user.custom_js = form.custom_js.data
                db.session.commit()
                flash('Setting updated.', 'success')
                return redirect(url_for('blog.index'))

    return render_template('admin/settings.html', form=form)


# settings end


# post start
@bp_admin.route('/post/manage')
def manage_posts() -> Response | str:
    page: int = request.args.get('page', 1, type=int)
    pagination: Pagination = db.paginate(
        select(Post).order_by(Post.created_time.desc()),
        page=page,
        per_page=current_app.config['GREYBOOK_MANAGE_POST_PER_PAGE'],
        error_out=False,
    )
    if page > pagination.pages:
        return redirect(url_for('.manage_post', page=pagination.pages))

    posts: list[Post] = pagination.items
    return render_template('admin/manage_post.html', page=page, pagination=pagination, posts=posts)


@bp_admin.route('/post/new', methods=['GET', 'POST'])
def new_post() -> Response | str:
    form = PostForm()
    match request.method:
        case 'GET':
            pass
        case 'POST':
            if form.validate_on_submit():
                post: Post = Post.from_form(form)
                db.session.add(post)
                db.session.commit()
                flash('Post created.', 'success')
                return redirect(url_for('blog.show_post', post_id=post.id))

    return render_template('admin/new_post.html', form=form)


@bp_admin.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id: int) -> Response | str:
    post: Post = db.get_or_404(Post, post_id)
    match request.method:
        case 'GET':
            form: PostForm = PostForm.from_model(post)
        case 'POST':
            form = PostForm()
            if form.validate_on_submit():
                post.edit_from_form(form)
                db.session.commit()
                flash('Post updated.', 'success')
                return redirect(url_for('blog.show_post', post_id=post.id))

    return render_template('admin/edit_post.html', form=form)


@bp_admin.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id: int) -> Response:
    post: Post = db.get_or_404(Post, post_id)
    post.delete()
    flash('Post deleted.', 'success')
    return redirect_back()


@bp_admin.route('/post/<int:post_id>/set-comment', methods=['POST'])
def set_comment(post_id: int) -> Response:
    post: Post = db.get_or_404(Post, post_id)
    post.no_comment = not post.no_comment  # type: ignore
    db.session.commit()
    flash(f'Comment {'disabled' if post.no_comment else 'enabled'}.', 'success')  # type: ignore
    return redirect_back()


# post end


# comment start
@bp_admin.route('/comment/manage')
def manage_comments() -> Response | str:
    filter_rule: str = request.args.get('filter', 'all')  # 'all', 'unread', 'admin'
    page: int = request.args.get('page', 1, type=int)
    per_page: int = current_app.config['GREYBOOK_COMMENT_PER_PAGE']

    match filter_rule:
        case 'unread':
            filtered_comments: Select[tuple[Comment]] = select(Comment).filter_by(reviewed=False)
        case 'admin':
            filtered_comments = select(Comment).filter_by(from_admin=True)
        case _:
            filtered_comments = select(Comment)

    pagination: Pagination = db.paginate(
        filtered_comments.order_by(Comment.created_time.desc()),
        page=page,
        per_page=per_page,
        error_out=False,
    )
    if page > pagination.pages:
        return redirect(url_for('.manage_comments', page=pagination.pages, filter=filter_rule))

    comments: list[Comment] = pagination.items
    return render_template('admin/manage_comment.html', comments=comments, pagination=pagination)


@bp_admin.route('/comment/<int:comment_id>/approve', methods=['POST'])
def approve_comment(comment_id: int) -> Response:
    comment: Comment = db.get_or_404(Comment, comment_id)
    comment.review()
    db.session.commit()
    flash('Comment published.', 'success')
    return redirect_back()


@bp_admin.route('/comment/approve', methods=['POST'])
def approve_all_comments() -> Response:
    for comment in db.session.scalars(select(Comment).filter_by(reviewed=False)):
        comment.review()
    db.session.commit()
    flash('All comments published.', 'success')
    return redirect_back()


@bp_admin.route('/comment/<int:comment_id>/delete', methods=['POST'])
def delete_comment(comment_id: int) -> Response:
    comment: Comment = db.get_or_404(Comment, comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'success')
    return redirect_back()


# comment end


# category start
@bp_admin.route('/category/manage')
def manage_categories() -> str:
    return render_template('admin/manage_category.html')


@bp_admin.route('/category/new', methods=['GET', 'POST'])
def new_category() -> Response | str:
    form = CategoryForm()
    if form.validate_on_submit():
        category: Category = Category.from_form(form)
        db.session.add(category)
        db.session.commit()
        flash('Category created.', 'success')
        return redirect(url_for('.manage_categories'))

    return render_template('admin/new_category.html', form=form)


@bp_admin.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id: int) -> Response | str:
    if category_id == 1:
        flash('You can not edit the default category.', 'warning')
        return redirect(url_for('blog.index'))

    form = CategoryForm()
    category: Category = db.get_or_404(Category, category_id)
    if form.validate_on_submit():
        category.edit_from_form(form)
        flash('Category updated.', 'success')
        return redirect(url_for('.manage_categories'))

    if request.method == 'GET':
        form.name.data = category.name  # type: ignore
    return render_template('admin/edit_category.html', form=form)


@bp_admin.route('/category/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id: int) -> Response:
    category: Category = db.get_or_404(Category, category_id)
    if category.delete():
        flash('Category deleted.', 'success')
        return redirect(url_for('.manage_categories'))

    flash('You can not delete the default category.', 'warning')
    return redirect(url_for('blog.index'))


# category end


# link start
@bp_admin.route('/link/manage', methods=['GET', 'POST'])
def manage_link():
    return render_template('admin/manage_link.html')


@bp_admin.route('/link/new', methods=['GET', 'POST'])
def new_link() -> Response | str:
    form = LinkForm()
    if form.validate_on_submit():
        link: Link = Link.from_form(form)
        db.session.add(link)
        db.session.commit()
        flash('Link created.', 'success')
        return redirect(url_for('.manage_link'))

    return render_template('admin/new_link.html', form=form)


@bp_admin.route('/link/<int:link_id>/edit', methods=['GET', 'POST'])
def edit_link(link_id: int) -> Response | str:
    form = LinkForm()
    link: Link = db.get_or_404(Link, link_id)
    if form.validate_on_submit():
        link.edit_from_form(form)
        flash('Link updated.', 'success')
        return redirect(url_for('.manage_link'))

    if request.method == 'GET':
        form.name.data = link.name  # type: ignore
        form.url.data = link.url  # type: ignore
    return render_template('admin/edit_link.html', form=form)


@bp_admin.route('/link/<int:link_id>/delete', methods=['POST'])
def delete_link(link_id: int) -> Response:
    link: Link = db.get_or_404(Link, link_id)
    db.session.delete(link)
    db.session.commit()
    flash('Link deleted.', 'success')
    return redirect(url_for('.manage_link'))


# link end


# upload start
@bp_admin.route('/upload', methods=['POST'])
def upload_image() -> Response:
    file: FileStorage = request.files['upload']
    if not allowed_file(file.filename):  # type: ignore
        return upload_fail('Image only!')

    filename: str = random_filename(file.filename)  # type: ignore
    file.save(os.path.join(current_app.config['GREYBOOK_UPLOAD_PATH'], filename))
    return upload_success(
        url_for('blog.get_image', filename=filename),
        filename,
    )


# upload end
