import os
import uuid
from urllib.parse import (
    ParseResult,
    urljoin,
    urlparse,
)

from flask import (
    current_app,
    redirect,
    request,
    url_for,
)
from werkzeug.wrappers.response import Response


def is_safe_url(target: str) -> bool:
    """
    Check if the target URL is safe to redirect to.

    Parameters
    ----------
    target : str
        A URL to check.

    Returns
    -------
    bool
        True if the target URL is safe.
    """
    ref_url: ParseResult = urlparse(request.host_url)
    test_url: ParseResult = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def redirect_back(default: str = 'blog.index', /, **kwargs) -> Response:
    """
    If no 'next' arg or referrer is provided in the request, the function will redirect to the default page.

    Parameters
    ----------
    default : str, optional
        Default page to redirect to, by default 'blog.index'

    **kwargs : optional
        These kwargs will be passed to the url_for function to generate the default redirect URL.

    Returns
    -------
    Response
        Redirect response.
    """
    for target in request.args.get('next'), request.referrer:
        if target and is_safe_url(target):
            return redirect(target)

    return redirect(url_for(default, **kwargs))


def allowed_file(filename: str) -> bool:
    """
    Check if the filename is allowed for image upload.

    Parameters
    ----------
    filename : str
        Image filename.

    Returns
    -------
    bool
        True if the filename is allowed.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['GREYBOOK_ALLOWED_IMAGE_EXTENSIONS']


def random_filename(old_filename: str) -> str:
    """
    Generate a new random filename for the uploaded image.

    Parameters
    ----------
    old_filename : str
        The original filename of the uploaded image.

    Returns
    -------
    str
        The new filename with a random UUID.
    """
    ext = os.path.splitext(old_filename)[1]
    return f'{uuid.uuid4().hex}{ext}'
