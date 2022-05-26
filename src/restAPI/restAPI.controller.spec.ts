import { Test, TestingModule } from '@nestjs/testing';
import { RestApiController } from './restAPI.controller';

import { ConfigModule } from '@nestjs/config';
import { RestApiModule } from './restAPI.module';

describe('RestApi Controller', () => {
  let controller: RestApiController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [
        RestApiModule,
        ConfigModule.forRoot({
          isGlobal: true,
          envFilePath: process.env.NODE_ENV + '.env',
        }),
      ],
    }).compile();

    controller = module.get<RestApiController>(RestApiController);
  });

  describe('/rest', () => {
    it('should return directory JSON listing properly"', async () => {
      const webhookOutput = await controller.rest(
        'devopslibrary',
        'sampledata',
        { '0': '/datacenters', path: 'rest' },
        false,
      );

      expect(webhookOutput).toMatchObject([
        {
          name: 'Indianapolis Production Datacenter 01',
          lastUpdated: '2020-12-30T19:31:99Z',
          shortname: 'ind01pr',
          dns: { primary: '8.8.8.8', secondary: '4.2.2.9' },
          cidr: '172.16.0.0/19',
          vlans: [1, 2, 3, 4, 5],
        },
        {
          name: 'San Diego Disaster Recovery Datacenter 01',
          lastUpdated: '2019-12-30T19:31:42Z',
          shortname: 'san01dr',
          dns: { primary: '1.1.1.1', secondary: '2.2.2.2' },
          cidr: '172.32.0.0/19',
          vlans: [6, 7, 8, 9, 10],
        },
        {
          name: 'San Francisco Production Datacenter 01',
          lastUpdated: '2019-12-30T19:34:41Z',
          shortname: 'sfo01pr',
          dns: { primary: '9.9.9.9', secondary: '12.12.12.12' },
          cidr: '172.64.0.0/19',
          vlans: [11, 12, 13, 14, 15],
        },
      ]);
    });
    it('should return directory JSON filtered with query params properly"', async () => {
      const webhookOutput = await controller.rest(
        'devopslibrary',
        'sampledata',
        { '0': '/datacenters', path: 'rest' },
        { shortname: 'ind01pr' },
      );

      expect(webhookOutput).toMatchObject([
        {
          name: 'Indianapolis Production Datacenter 01',
          lastUpdated: '2020-12-30T19:31:99Z',
          shortname: 'ind01pr',
          dns: { primary: '8.8.8.8', secondary: '4.2.2.9' },
          cidr: '172.16.0.0/19',
          vlans: [1, 2, 3, 4, 5],
        },
      ]);
    });
    it('should return resource JSON listing properly"', async () => {
      const webhookOutput = await controller.rest(
        'devopslibrary',
        'sampledata',
        { '0': '/datacenters/ind01pr', path: 'rest' },
        false,
      );
      expect(webhookOutput).toMatchObject({
        cidr: '172.16.0.0/19',
        dns: { primary: '8.8.8.8', secondary: '4.2.2.9' },
        lastUpdated: '2020-12-30T19:31:99Z',
        name: 'Indianapolis Production Datacenter 01',
        shortname: 'ind01pr',
        vlans: [1, 2, 3, 4, 5],
      });
    });
  });
});
