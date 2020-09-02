from flask import request
from functools import wraps
from jose import jwt
import requests

AUTH0_DOMAIN = 'dev-h3vh5vn4.eu.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'http://localshost:5000'

# AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


# Auth Header

auth0_client_secret = "qmukm5wFdA1viqeY0lTqrvrITDxhSxro"
auth0_client_id = "qmukm5wFdA1viqeY0lTqrvrITDxhSxro"
auth0_domain = "dev-h3vh5vn4.eu.auth0.com"
'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''


def get_token_auth_header():
    auth = request.headers.get('Authorization') if 'Authorization' in request.headers else None
    spliced_auth = auth.split() if auth else None
    if not auth:
        raise AuthError({
            'code': 'invalid auth header',
            'description': 'authorization header is expected in request'
        }, status_code=401)
    bearer_part = auth.split()[0]
    if not bearer_part or (bearer_part and bearer_part.lower() != 'bearer'):
        raise AuthError({
            'code': 'invalid auth header',
            'description': 'authorization must be bearer -- (Authorization Bearer)'
        }, status_code=401)

    # contains Bearer with no token part
    if len(spliced_auth) == 1:
        raise AuthError({
            'code': 'token not found',
            'description': 'token not found in header'
        }, status_code=401)

    if len(spliced_auth) > 2:
        raise AuthError({
            'code': 'invalid header',
            'description': 'authorization type must be bearer'
        }, status_code=401)
    token = auth.split()[1]
    return token


'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload
    it should raise an AuthError if permissions are not included in the payload
    !!NOTE check your RBAC settings in Auth0 it should raise an AuthError if the requested 
    permission string is not in the payload permissions array
    return true otherwise
'''


def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid claims',
            'description': 'permissions not present in jwt'
        }, status_code=401)
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'invalid permission',
            'description': 'you dont have the permission to view this resource'
        }, status_code=401)
    return True


'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''


def verify_decode_jwt(token):
    # get the unverified token and compare
    unverified_header = ''
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({
            'code': 'invalid token',
            'description': 'please confirm that token is a jwt token!!'
        }, status_code=401)

    url = f' https://{AUTH0_DOMAIN}/.well-known/jwks.json'
    keys_request = requests.get(f' https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = None
    if keys_request.status_code == 200:
        jwks = keys_request.json()
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid auth header',
            'description': 'invalid authorization token'
        }, status_code=401)

    if jwks:
        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = key
        if rsa_key:
            try:
                issuer = f'https://{AUTH0_DOMAIN}/'
                decoded = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=API_AUDIENCE,
                    issuer=issuer
                )
                return decoded
            except jwt.ExpiredSignatureError:
                raise AuthError({
                    'code': 'token expired',
                    'description': 'api token has expired'
                }, status_code=401)
            except jwt.JWTClaimsError:
                raise AuthError({
                    'code': 'invalid_claims',
                    'description': 'Incorrect claims. Please, check the audience and issuer.'
                }, 401)
            except Exception:
                raise AuthError({
                    'code': 'invalid auth token',
                    'description': 'please make sure the token is correct.'
                }, 401)
        raise AuthError({
            'code': 'invalid token',
            'description': 'please provide a valid token.'
        }, 401)
    raise AuthError({
        'code': 'error validating token',
        'description': 'error validating token.'
    }, 401)


'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator
