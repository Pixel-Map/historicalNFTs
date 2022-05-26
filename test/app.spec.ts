import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import request from 'supertest';
import { AppModule } from '../src/app.module';
import fs from 'fs';

describe('AppController (e2e)', () => {
  let app: INestApplication;

  beforeEach(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();
  });

  it('/swagger/devopslibrary/sampledata (GET) should return proper schema JSON', async () => {
    const expectedJson = await JSON.parse(
      fs.readFileSync(__dirname + '/swagger.json', 'utf-8'),
    );
    const response = await request(app.getHttpServer()).get(
      '/swagger.json/devopslibrary/sampledata',
    );

    const parsedResponse = await JSON.parse(response.text);
    expect(parsedResponse).toEqual(expectedJson);
  }, 10000);

  afterAll(() => {
    app.close();
  });
});
