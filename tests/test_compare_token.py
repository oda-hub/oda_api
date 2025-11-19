import pytest

@pytest.mark.parametrize('tokens_tems', [[100, 100],
                                         [100, 150],
                                         [150, 100]])
@pytest.mark.parametrize('tokens_intsubs', [[100, 100],
                                            [100, 150],
                                            [150, 100]])
@pytest.mark.parametrize('tokens_mstouts', [True, False])
@pytest.mark.parametrize('tokens_mssubs', [True, False])
@pytest.mark.parametrize('tokens_msdones', [True, False])
@pytest.mark.parametrize('tokens_fails', [True, False])
@pytest.mark.parametrize('missing_keys', [True, False])
@pytest.mark.parametrize('extra_keys', [True, False])
@pytest.mark.parametrize('tokens_subs', [['sub1', 'sub1'],
                                         ['sub1', 'sub2'],
                                         ['sub2', 'sub1']])
@pytest.mark.parametrize('tokens_emails', [['email1', 'email1'],
                                           ['email1', 'email2'],
                                           ['email2', 'email1']
                                           ])
@pytest.mark.parametrize('tokens_roles', [[[], ['role1', 'role2']],
                                          [['role1', 'role2'], []],
                                          [['role1', 'role2'], ['role1', 'role2']],
                                          [['role1', 'role2'], ['role1', 'role3', 'role4']],
                                          [['role1', 'role2'], ['role1', 'role2', 'role3']],
                                          [['role1', 'role2', 'role3'], ['role1', 'role2']],
                                          [[], []]
                                          ])
@pytest.mark.parametrize('tokens_exps', [[100, 100],
                                         [100, 150],
                                         [150, 100]
                                         ])
def test_compare_token(tokens_tems, tokens_intsubs, tokens_mstouts, tokens_mssubs, tokens_msdones, tokens_fails,
                       missing_keys, extra_keys, tokens_subs, tokens_emails, tokens_roles, tokens_exps):
    from oda_api.token import token_email_options_numeric, token_email_options_flags, compare_token

    token1_payload = {
        "sub": tokens_subs[0],
        "email": tokens_emails[0],
        "exp": tokens_exps[0],
        "roles": tokens_roles[0],
        # email options
        "tem": tokens_tems[0],
        "intsub": tokens_intsubs[0],
        "mssub": tokens_mssubs,
        "msdone": tokens_msdones,
        "mstout": tokens_mstouts,
        "msfail": tokens_fails
    }

    token2_payload = {
        'sub': tokens_subs[1],
        'email': tokens_emails[1],
        'exp': tokens_exps[1],
        'roles': tokens_roles[1],
        # email options
        "tem": tokens_tems[1],
        "intsub": tokens_intsubs[1],
        "mssub": tokens_mssubs,
        "msdone": tokens_msdones,
        "mstout": tokens_mstouts,
        "msfail": tokens_fails
    }

    if missing_keys:
        token1_payload.pop('sub')

    if extra_keys:
        token1_payload['extra_key'] = 'test'

    comparison_result = compare_token(token1_payload, token2_payload)

    assert 'missing_keys' in comparison_result
    if missing_keys:
        assert comparison_result['missing_keys'] == ['sub']
    else:
        assert comparison_result['missing_keys'] == []

    assert 'extra_keys' in comparison_result
    if extra_keys:
        assert comparison_result['extra_keys'] == ['extra_key']
    else:
        assert comparison_result['extra_keys'] == []

    assert 'exp' in comparison_result
    if tokens_exps[0] > tokens_exps[1]:
        assert comparison_result['exp'] == 1
    elif tokens_exps[0] < tokens_exps[1]:
        assert comparison_result['exp'] == -1
    elif tokens_exps[0] == tokens_exps[1]:
        assert comparison_result['exp'] == 0

    assert 'roles' in comparison_result
    token1_roles_difference = set(token1_payload["roles"]) - set(token2_payload["roles"])
    token2_roles_difference = set(token2_payload["roles"]) - set(token1_payload["roles"])
    if token1_roles_difference != set() and token2_roles_difference == set():
        assert comparison_result["roles"] == 1
    elif len(token1_roles_difference) < len(token2_roles_difference) or \
            (len(token1_roles_difference) >= len(token2_roles_difference) and token2_roles_difference != set()):
        assert comparison_result["roles"] == -1
    elif len(token1_roles_difference) == len(token2_roles_difference) and \
            token1_roles_difference == set() and token2_roles_difference == set():
        assert comparison_result["roles"] == 0

    if not missing_keys:
        assert 'sub' in comparison_result
        if tokens_subs[0] == tokens_subs[1]:
            assert comparison_result['sub']
        else:
            assert not comparison_result['sub']
    else:
        assert 'sub' not in comparison_result

    assert 'email' in comparison_result
    if tokens_emails[0] == tokens_emails[1]:
        assert comparison_result['email']
    else:
        assert not comparison_result['email']

    # check email options
    for opt in token_email_options_numeric:
        assert opt in comparison_result
        if token1_payload[opt] > token2_payload[opt]:
            assert comparison_result[opt] == 1
        elif token1_payload[opt] < token2_payload[opt]:
            assert comparison_result[opt] == -1
        else:
            assert comparison_result[opt] == 0

    for opt in token_email_options_flags:
        assert opt in comparison_result
        if token1_payload[opt] == token2_payload[opt]:
            assert comparison_result[opt]
        else:
            assert not comparison_result[opt]