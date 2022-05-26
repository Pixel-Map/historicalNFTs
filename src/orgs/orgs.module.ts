import { Module, HttpModule } from '@nestjs/common';
import { OrgsController } from './orgs.controller';
import { OrgsService } from './orgs.service';

@Module({
  imports: [HttpModule],
  controllers: [OrgsController],
  providers: [OrgsService],
})
export class OrgsModule {}
