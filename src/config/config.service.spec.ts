import { Test, TestingModule } from '@nestjs/testing';
import { ConfigService } from './config.service';
import { ConfigModule } from './config.module';

describe('ConfigService', () => {
  let service: ConfigService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [ConfigModule],
    }).compile();
    service = module.get<ConfigService>(ConfigService);
  });

  it('should be defined', () => {
    expect(service.get('DOMAIN')).toBe('localhost');
  });
});
