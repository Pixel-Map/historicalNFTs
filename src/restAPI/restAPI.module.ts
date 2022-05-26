import { Module } from '@nestjs/common';
import { RestApiController } from './restAPI.controller';
import { RestApiService } from './restAPI.service';
import { SchemaModule } from '../schema/schema.module';

@Module({
  controllers: [RestApiController],
  providers: [RestApiService],
  imports: [SchemaModule],
})
export class RestApiModule {}
