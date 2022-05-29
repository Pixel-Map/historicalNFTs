import { Module } from '@nestjs/common';
import { RestApiController } from './restAPI.controller';
import { RestApiService } from './restAPI.service';

@Module({
  controllers: [RestApiController],
  providers: [RestApiService],
})
export class RestApiModule {}
