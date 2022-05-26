import { Module, MiddlewareConsumer } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { SwaggerModule } from './swagger/swagger.module';
import { RestApiModule } from './restAPI/restAPI.module';
import { RestApiController } from './restAPI/restAPI.controller';
import { RestApiService } from './restAPI/restAPI.service';
import { LoggerMiddleware } from './logger.middleware';
import { TerminusModule } from '@nestjs/terminus';
import { HealthController } from './health/health.controller';
import { SchemaModule } from './schema/schema.module';
import { ServeStaticModule } from '@nestjs/serve-static';

@Module({
  imports: [
    ServeStaticModule.forRoot({
      rootPath: ".",
      renderPath: "."
    }),

    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: process.env.NODE_ENV + '.env',
    }),
    SwaggerModule,
    RestApiModule,
    TerminusModule,
    SchemaModule,
  ],
  controllers: [
    RestApiController,
    HealthController,
  ],
  providers: [RestApiService],
})
export class AppModule {
  configure(consumer: MiddlewareConsumer) {
    consumer.apply(LoggerMiddleware).forRoutes('*');
  }
}

