import { Test, TestingModule } from '@nestjs/testing';
import { OrgsService } from './orgs.service';
import { ConfigService } from '../config/config.service';
import { ConfigModule } from '../config/config.module';
import { OrgsModule } from './orgs.module';

describe('OrgsService', () => {
  let service: OrgsService;
  let config: ConfigService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [ConfigModule, OrgsModule],
    }).compile();

    config = module.get<ConfigService>(ConfigService);
    service = module.get<OrgsService>(OrgsService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should return all orgs a user is a part of', async () => {
    const token = config.get('CLONE_TOKEN');
    const githubUser = {
      token,
      provider: 'github',
      user_id: 5382669,
      connection: 'github',
      isSocial: true,
    };
    const output = await service.getUserOrgs(githubUser);
    expect(output[0]).toHaveProperty('description');
    expect(output[0]).toHaveProperty('repos_url');
  });

  it('should return all repositories user has access to within an org', async () => {
    const token = config.get('CLONE_TOKEN');
    const githubUser = {
      token,
      provider: 'github',
      user_id: 5382669,
      connection: 'github',
      isSocial: true,
    };
    const output = await service.getUserReposWithinOrg(
      'devopslibrary',
      githubUser,
    );
    expect(output[0]).toHaveProperty('id');
    expect(output[0]).toHaveProperty('node_id');
    expect(output[0]).toHaveProperty('name');
    expect(output[0]).toHaveProperty('full_name');
    expect(output[0]).toHaveProperty('owner');
  });
});
