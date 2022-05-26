import { Module, MiddlewareConsumer, HttpModule } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { SwaggerModule } from './swagger/swagger.module';
import { RestApiModule } from './restAPI/restAPI.module';
import { RestApiController } from './restAPI/restAPI.controller';
import { RestApiService } from './restAPI/restAPI.service';
import { LoggerMiddleware } from './logger.middleware';
import { OrgsController } from './orgs/orgs.controller';
import { OrgsService } from './orgs/orgs.service';
import { TerminusModule } from '@nestjs/terminus';
import { HealthController } from './health/health.controller';
import { SchemaModule } from './schema/schema.module';
import { ServeStaticModule } from '@nestjs/serve-static';

@Module({
  imports: [
    ServeStaticModule.forRoot({
      rootPath: "nfts/",
      renderPath: "images"
    }),
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: process.env.NODE_ENV + '.env',
    }),
    SwaggerModule,
    RestApiModule,
    HttpModule,
    TerminusModule,
    SchemaModule,
  ],
  controllers: [
    RestApiController,
    OrgsController,
    HealthController,
  ],
  providers: [RestApiService, OrgsService],
})
export class AppModule {
  configure(consumer: MiddlewareConsumer) {
    consumer.apply(LoggerMiddleware).forRoutes('*');
  }
}

