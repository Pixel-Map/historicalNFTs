import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { NestExpressApplication } from '@nestjs/platform-express';
const swaggerUi = require('swagger-ui-express');
import {join} from 'path'

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule, {
    logger: ['log', 'error', 'debug', 'verbose', 'warn'],
  });
  app.enableCors();
  app.set('json spaces', 2);

  // Swagger
  const swaggerDocument = require('nft_schema.json');
  app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

  await app.listen(3000);
}
bootstrap();
