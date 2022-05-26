import { Test, TestingModule } from '@nestjs/testing';
import { SwaggerService } from './swagger.service';
import { ConfigModule } from '@nestjs/config';
import { SwaggerModule } from './swagger.module';
const SwaggerParser = require('swagger-parser');

describe('SwaggerService', () => {
  let swaggerService: SwaggerService;

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

    swaggerService = module.get<SwaggerService>(SwaggerService);
  });

  describe('getSwagger', () => {
    it('should be generated successfully', async () => {
      const swaggerJSON = await swaggerService.getSwagger(
        'devopslibrary/sampledata',
      );
      expect(swaggerJSON).toBeDefined();
      const api = await SwaggerParser.validate(JSON.parse(swaggerJSON));
      expect(api.info.title).toBe('devopslibrary/sampledata');
      expect(api.info.version).toBe('1.0.0');
    });
  });
});
