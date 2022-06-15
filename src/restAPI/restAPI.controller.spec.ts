import { RestApiService } from './restAPI.service';

describe('RestAPIService', () => {
  let restApiService: RestApiService;

  beforeEach(() => {
    restApiService = new RestApiService();
  });

  describe('getGrade', () => {
    it('should return the correct grade for a given NFT', async () => {

      const nftData = await restApiService.getData('/', false)
      let grades = []
      let scores = []
      for (const nft of nftData) {
        const score = restApiService.getScore(nft);
        const grade = restApiService.getGrade(score)
        grades.push(nft.title + " - " + grade)
        scores.push(score)
      }
      console.log(grades)
      const average = scores.reduce((a, b) => a + b) / scores.length;

      console.log("Average: " + restApiService.getGrade(average))
      // expect(grade).toBe('A');
    });
  });

} )
