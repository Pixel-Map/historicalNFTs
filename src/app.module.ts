import { Module, MiddlewareConsumer, CacheModule, CacheInterceptor } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { SwaggerModule } from './swagger/swagger.module';
import { RestApiModule } from './restAPI/restAPI.module';
import { RestApiController } from './restAPI/restAPI.controller';
import { RestApiService } from './restAPI/restAPI.service';
import { LoggerMiddleware } from './logger.middleware';
import { TerminusModule } from '@nestjs/terminus';
import { HealthController } from './health/health.controller';
import { ServeStaticModule } from '@nestjs/serve-static';
import { APP_INTERCEPTOR } from '@nestjs/core';

@Module({
  imports: [
    ServeStaticModule.forRoot({
      rootPath: ".",
      renderPath: "."
    }),
    CacheModule.register(
      {isGlobal: true, ttl: 9999999}
    ),

    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: process.env.NODE_ENV + '.env',
    }),
    SwaggerModule,
    RestApiModule,
    TerminusModule,
  ],
  controllers: [
    RestApiController,
    HealthController,
  ],
  providers: [RestApiService, {
    provide: APP_INTERCEPTOR,
    useClass: CacheInterceptor,
  },],
})
export class AppModule {
  configure(consumer: MiddlewareConsumer) {
    consumer.apply(LoggerMiddleware).forRoutes('*');
  }
}

