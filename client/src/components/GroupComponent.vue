<template>
  <div class="columns">
    <div class="column is-2">
      <GroupNavbar />
    </div>
    <div class="column">
      <h3 class="title">Groupe {{ $route.params.groupName }}</h3>
      <div class="box">
        <form v-on:submit.prevent="postGroup">
          <div class="table-container">
            <table class="table is-fullwidth is-striped">
              <tr v-for="match in groupResource" :key="match['id']">
                <td>{{ match["team1"]["description"] }}</td>
                <td>
                  <input class="input is-small" min="0" type="number" v-model="match['team1']['score']">
                </td>
                <td>
                  <input class="input is-small" min="0" type="number" v-model="match['team2']['score']">
                </td>
                <td>{{ match["team2"]["description"] }}</td>
              </tr>
            </table>
          </div>
          <div>
            <button class="button is-dark">Valider</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import _ from 'lodash';
import GroupNavbar from './GroupNavbar.vue';

export default {
  name: 'GroupComponent',
  components: {
    GroupNavbar,
  },
  data() {
    return {
      groupResource: [],
      // keep copy of group resource to send only PATCH /match of the updated matches
      groupResourceCopy: [],
    };
  },
  methods: {
    getGroup(groupName) {
      this.$store.dispatch('getGroup', { groupName })
        .then((res) => {
          this.groupResource = res.data.result;
          this.groupResourceCopy = JSON.parse(JSON.stringify(res.data.result));
        });
    },
    postGroup() {
      for (let index = 0; index < this.groupResource.length; index += 1) {
        if (!_.isEqual(this.groupResource[index], this.groupResourceCopy[index])) {
          if (this.groupResource[index].team1.score === '') {
            this.groupResource[index].team1.score = null;
          }
          if (this.groupResource[index].team2.score === '') {
            this.groupResource[index].team2.score = null;
          }
          this.$store.dispatch('patchScores', { matchId: this.groupResource[index].match_id, matchResource: this.groupResource[index] });
        }
      }
      this.groupResourceCopy = JSON.parse(JSON.stringify(this.groupResource));
    },
  },
  beforeRouteUpdate(to, from, next) {
    this.getGroup(to.params.groupName);
    next();
  },
  created() {
    this.getGroup(this.$route.params.groupName);
  },
};

</script>
