import { Module } from '@nestjs/common';
import { SwaggerService } from './swagger.service';
import { SwaggerController } from './swagger.controller';
import { SchemaModule } from '../schema/schema.module';

@Module({
  providers: [SwaggerService],
  imports: [SchemaModule],
  controllers: [SwaggerController],
})
export class SwaggerModule {}
