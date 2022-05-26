import { Test, TestingModule } from '@nestjs/testing';
import { SwaggerController } from './swagger.controller';
import { ConfigModule } from '@nestjs/config';
import { SwaggerModule } from './swagger.module';

describe('Swagger Controller', () => {
  let controller: SwaggerController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [
        SwaggerModule,
        ConfigModule.forRoot({
          isGlobal: true,
          envFilePath: process.env.NODE_ENV + '.env',
        }),
      ],
    }).compile();

    controller = module.get<SwaggerController>(SwaggerController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});
