import { Test, TestingModule } from '@nestjs/testing';
import { SchemaService } from './schema.service';

describe('SchemaService', () => {
  let service: SchemaService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [SchemaService],
    }).compile();

    service = module.get<SchemaService>(SchemaService);
  });

  describe('getCommonPropertiesWithinArray', () => {
    it('should return all common properties (key with value of type)', async () => {
      const keys = await service.getCommonPropertiesWithinArray([
        {
          count: 500,
          name: 'Old Legacy Application',
          serverType: 'iis',
          teamOwner: 'webdev',
        },
        {
          count: 14,
          extraInformation: 'This should not get picked up.',
          name: 'New Backend Application',
          serverType: 'node',
          teamOwner: 'devteam',
        },
      ]);
      expect(keys).toEqual([
        {
          name: 'count',
          type: 'number',
        },
        {
          name: 'name',
          type: 'string',
        },
        {
          name: 'serverType',
          type: 'string',
        },
        {
          name: 'teamOwner',
          type: 'string',
        },
      ]);
    });
  });

  describe('isDataValid', () => {
    it('should return true when the data matches the schema', async () => {
      const output = await service.isDataValid('./test/fixtures/fakeData', {
        name: 'Test Application',
        serverType: 'java',
        teamOwner: 'webdev',
        count: 100,
      });
      expect(output).toBe(true);
    });
  });

  describe('getSchema', () => {
    it('should return generated schema if possible', async () => {
      const schema = service.getSchema('./test/fixtures/fakeData');
      expect(schema).toEqual({
        $id: 'fakeData',
        $schema: 'http://json-schema.org/draft-07/schema#',
        definitions: {},
        properties: {
          count: {
            default: 0,
            title: 'The count Schema',
            type: 'number',
          },
          name: {
            default: '',
            pattern: '^(.*)$',
            title: 'The name Schema',
            type: 'string',
          },
          serverType: {
            default: '',
            pattern: '^(.*)$',
            title: 'The serverType Schema',
            type: 'string',
          },
          teamOwner: {
            default: '',
            pattern: '^(.*)$',
            title: 'The teamOwner Schema',
            type: 'string',
          },
        },
        required: ['name', 'serverType', 'teamOwner', 'count'],
        title: 'fakeData',
        type: 'object',
      });
    });
    it('should return the existing schema if it exists', async () => {
      const schema = service.getSchema('./test/fixtures/fakeRepoWithSchema');
      expect(schema).toEqual({
        $id: 'http://example.com/root.json',
        $schema: 'http://json-schema.org/draft-07/schema#',
        definitions: {},
        properties: {
          name: {
            default: '',
            pattern: '^(.*)$',
            title: 'The Name Schema',
            type: 'string',
          },
        },
        required: ['name'],
        title: 'Datacenter',
        type: 'object',
      });
    });
  });

  describe('generateSchema', () => {
    it('should return generated schema when it scans a folder with multiple JSON files', async () => {
      const schema = service.generateSchema('./test/fixtures/fakeData');
      expect(schema).toEqual({
        $id: 'fakeData',
        $schema: 'http://json-schema.org/draft-07/schema#',
        definitions: {},
        properties: {
          count: {
            default: 0,
            title: 'The count Schema',
            type: 'number',
          },
          name: {
            default: '',
            pattern: '^(.*)$',
            title: 'The name Schema',
            type: 'string',
          },
          serverType: {
            default: '',
            pattern: '^(.*)$',
            title: 'The serverType Schema',
            type: 'string',
          },
          teamOwner: {
            default: '',
            pattern: '^(.*)$',
            title: 'The teamOwner Schema',
            type: 'string',
          },
        },
        required: ['name', 'serverType', 'teamOwner', 'count'],
        title: 'fakeData',
        type: 'object',
      });
    });
  });
  describe('loadJSONinFolder', () => {
    it('should load all JSON within a folder and return as array of objects', async () => {
      const loadedJSON = service.loadJSONinFolder('./test/fixtures/fakeData');
      expect(loadedJSON).toEqual([
        {
          count: 500,
          name: 'Old Legacy Application',
          serverType: 'iis',
          teamOwner: 'webdev',
        },
        {
          count: 14,
          extraInformation: 'This should not get picked up.',
          name: 'New Backend Application',
          serverType: 'node',
          teamOwner: 'devteam',
        },
      ]);
    });
  });

  describe('getCommonKeysWithinArrayOfObjects', () => {
    it('should retrieve ONLY the keys that are common across all objects within an array', async () => {
      const keys = service.getCommonKeysWithinArrayOfObjects([
        {
          count: 500,
          name: 'Old Legacy Application',
          serverType: 'iis',
          teamOwner: 'webdev',
        },
        {
          count: 14,
          extraInformation: 'This should not get picked up.',
          name: 'New Backend Application',
          serverType: 'node',
          teamOwner: 'devteam',
        },
      ]);
      expect(keys).toEqual(['count', 'name', 'serverType', 'teamOwner']);
    });
  });
});
