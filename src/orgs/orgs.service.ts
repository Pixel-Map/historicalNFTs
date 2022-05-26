import { Injectable, HttpService } from '@nestjs/common';

@Injectable()
export class OrgsService {
  constructor(private readonly httpService: HttpService) {}

  // Return all Orgs that a user belongs to
  public getUserOrgs(githubUser) {
    return this.httpService
      .get('https://api.github.com/user/orgs', {
        headers: { Authorization: `Bearer ${githubUser.token}` },
      })
      .toPromise()
      .then(orgs => {
        return orgs.data;
      });
  }

  // Return all repositories within an org that a user has access to
  public async getUserReposWithinOrg(org, githubUser) {
    let repos = [];
    let currentPage = 1;
    let finished = false;
    while (!finished) {
      const repoAPI = await this.httpService
        .get(
          'https://api.github.com/orgs/' +
            org +
            '/repos?per_page=100&page=' +
            currentPage,
          {
            headers: { Authorization: `Bearer ${githubUser.token}` },
          },
        )
        .toPromise();
      repos = repos.concat(repoAPI.data);
      if (
        !repoAPI.headers.link ||
        !repoAPI.headers.link.includes('rel="next"')
      ) {
        finished = true;
      }
      currentPage = currentPage + 1;
    }
    return repos;
  }
}
