import { Test, TestingModule } from '@nestjs/testing';
import { HealthController } from './health.controller';
import { TerminusModule } from '@nestjs/terminus';

describe('Health Controller', () => {
  let controller: HealthController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [HealthController],
      imports: [TerminusModule],
    }).compile();

    controller = module.get<HealthController>(HealthController);
  });

  it('should return succesfully', async () => {
    const health = await controller.check();
    expect(health).toEqual({
      details: {},
      error: {},
      info: {},
      status: 'ok',
    });
  });
});
