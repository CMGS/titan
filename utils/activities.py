#!/usr/local/bin/python2.7
#coding:utf-8

from sheep.api.local import reqcache

from query.repos import get_repo
from query.organization import get_team
from query.account import get_user, get_user_from_alias

from utils.helper import generate_list_page
from utils.repos import format_time, format_branch, get_url
from utils.timeline import get_repo_activities, get_organization_activities, \
        get_user_activities, get_team_activities

cache=reqcache
ACTIVITIES_PER_PAGE = 20

def render_push_action(action, organization, team=None, repo=None):
    repo = repo or cache.get(action['repo_id'], None) or get_repo(action['repo_id'])
    repo_url = cache.get('%d_url' % action['repo_id'])

    action['branch'] = format_branch(action['branch'])
    branch_url = cache.get('%d_branch_url' % action['repo_id'])

    if repo.tid > 0:
        team = team or get_team(repo.tid)
        repo_url = repo_url or get_url('repos.view', organization, repo, kw={'team': team,})
        branch_url = branch_url or get_url('repos.view', organization, repo, kw={'team': team,}, version=action['branch'])
    else:
        repo_url = repo_url or get_url('repos.view', organization, repo)
        branch_url = branch_url or get_url('repos.view', organization, repo, version=action['branch'])

    cache.set(action['repo_id'], repo)
    cache.set('%s_url' % action['repo_id'], repo_url)
    cache.set('%d_branch_url' % action['repo_id'], branch_url)
    action['repo'] = repo
    action['repo_url'] = repo_url
    action['branch_url'] = branch_url
    action['committer'] = get_user(action['committer_id'])
    length = len(action['data'])
    for i in xrange(0, length):
        log = action['data'][i]
        author = cache.get(log['author_email'], False)
        if author is False:
            author = get_user_from_alias(log['author_email'])
            cache.set(log['author_email'], author)
        log['author'] = author
        log['author_time'] = format_time(log['author_time'])
        log['message'] = log['message'].decode('utf8')

    if action['commits_num'] > length:
        action['more'] = True
    return action

def render_activities_page(page, t='repo', **kwargs):
    if t == 'repo':
        repo = kwargs['repo']
        activities = get_repo_activities(repo)
    elif t == 'organization':
        organization = kwargs['organization']
        activities = get_organization_activities(organization)
    elif t == 'team':
        team = kwargs['team']
        organization = kwargs['organization']
        activities = get_team_activities(organization, team)
    elif t == 'user':
        organization = kwargs['organization']
        uid = kwargs['uid']
        activities = get_user_activities(organization, uid)
    else:
        raise Exception('Not Implement %s Yet' % t)
    data = activities.get_activities(
                start=(page-1)*ACTIVITIES_PER_PAGE, \
                stop=page*ACTIVITIES_PER_PAGE-1, \
                withscores=True,
            )
    list_page = _get_list_page(activities, page)
    return data, list_page

def _get_list_page(activities, page=1):
    count = activities.count()
    has_prev = True if page > 1 else False
    has_next = True if page * ACTIVITIES_PER_PAGE < count else False
    pages = (count / ACTIVITIES_PER_PAGE) + 1
    list_page = generate_list_page(count, has_prev, has_next, page, pages)
    return list_page

