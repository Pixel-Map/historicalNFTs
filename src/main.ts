import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { NestExpressApplication } from '@nestjs/platform-express';

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule, {
    logger: ['log', 'error', 'debug', 'verbose', 'warn'],
  });
  app.enableCors();
  app.set('json spaces', 2);

  await app.listen(process.env.PORT || 3000);
}
bootstrap();
